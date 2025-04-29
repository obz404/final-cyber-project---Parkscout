import tensorflow as tf
import numpy as np
import cv2
import socket
import json
import sys
import os
import time
from aes_cipher import Cipher

# AES setup
AES_KEY = b'ThisIsASecretKey'
AES_NONCE = b'ThisIsASecretN'
cipher = Cipher(AES_KEY, AES_NONCE)

# Config
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 65432

# Command line args
SPOT_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 1
CAMERA_INDEX = int(sys.argv[2]) if len(sys.argv) > 2 else SPOT_ID - 1
HEADLESS = "--headless" in sys.argv

# Load model
model = tf.keras.models.load_model('ml_model/parking_model.h5')

# ROI crop area
CROP_X, CROP_Y, CROP_W, CROP_H = 140, 250, 360, 180

# Camera
cap = None if HEADLESS else cv2.VideoCapture(CAMERA_INDEX)

# --- Helpers ---

def get_current_status(spot_id):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_HOST, SERVER_PORT))
            request = {"action": "get_parking_spots"}
            s.send(cipher.aes_encrypt(json.dumps(request).encode()))
            response = cipher.aes_decrypt(s.recv(4096))
            data = json.loads(response)
            for spot in data.get("spots", []):
                if spot["id"] == spot_id:
                    return spot["status"]
    except:
        return None

def send_status_to_server(spot_id, status):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_HOST, SERVER_PORT))
            message = {
                "action": "update_parking_spot",
                "spot_id": spot_id,
                "status": status
            }
            encrypted = cipher.aes_encrypt(json.dumps(message).encode())
            s.send(encrypted)
            decrypted_response = cipher.aes_decrypt(s.recv(1024))
            response = json.loads(decrypted_response)
            print(f"🔁 Server response: {response}")
    except Exception as e:
        print(f"⚠️ Failed to contact server: {e}")

def save_status_locally(spot_id, status):
    status_data = {"spot_id": spot_id, "status": status}
    os.makedirs('static', exist_ok=True)
    with open(f'static/status_{spot_id}.json', 'w') as f:
        json.dump(status_data, f)

# --- Main Loop ---
while True:
    if HEADLESS:
        simulated_status = "available"
        send_status_to_server(SPOT_ID, simulated_status)
        save_status_locally(SPOT_ID, simulated_status)
        print(f"✅ Headless mode - Spot {SPOT_ID}: {simulated_status}")
        time.sleep(1)
        continue

    ret, frame = cap.read()
    if not ret:
        print(f"⚠️ Warning: Failed to grab frame for Spot {SPOT_ID}. Skipping update.")
        time.sleep(1)
        continue

    cropped = frame[CROP_Y:CROP_Y+CROP_H, CROP_X:CROP_X+CROP_W]
    resized = cv2.resize(cropped, (360, 102)) / 255.0
    input_img = np.expand_dims(resized, axis=0)

    prediction = model.predict(input_img)[0][0]
    predicted_status = "available" if prediction < 0.5 else "occupied"

    current_status = get_current_status(SPOT_ID)
    if current_status == "reserved":
        # Do not override reserved unless car is detected
        status = "reserved" if predicted_status == "available" else "occupied"
    else:
        status = predicted_status

    # === Visualization label and color ===
    if status == "reserved":
        label = "🅿️ RESERVED"
        color = (160, 32, 240)  # orange
    elif status == "occupied":
        label = "🚗 OCCUPIED"
        color = (0, 0, 255)  # red
    else:
        label = "🅿️ EMPTY"
        color = (0, 255, 0)  # green

    # Draw
    cv2.putText(frame, label, (CROP_X, CROP_Y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.rectangle(frame, (CROP_X, CROP_Y), (CROP_X + CROP_W, CROP_Y + CROP_H), color, 2)

    # Save for UI
    os.makedirs('static', exist_ok=True)
    cv2.imwrite(f'static/camera_feed_{SPOT_ID}.jpg', frame)

    send_status_to_server(SPOT_ID, status)
    save_status_locally(SPOT_ID, status)

    cv2.imshow(f"Spot {SPOT_ID} - Camera {CAMERA_INDEX}", frame)
    if cv2.waitKey(1000) & 0xFF == ord('q'):
        break

if cap:
    cap.release()
cv2.destroyAllWindows()
