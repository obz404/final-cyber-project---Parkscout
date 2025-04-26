import tensorflow as tf
import numpy as np
import cv2
import socket
import json
import sys
from aes_cipher import Cipher

# AES setup
AES_KEY = b'ThisIsASecretKey'
AES_NONCE = b'ThisIsASecretN'
cipher = Cipher(AES_KEY, AES_NONCE)

# Config
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 65432
SPOT_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 1
HEADLESS = "--headless" in sys.argv
CAMERA_INDEX = SPOT_ID - 1

# Load model
model = tf.keras.models.load_model('ml_model/parking_model.h5')

# ROI
CROP_X, CROP_Y, CROP_W, CROP_H = 140, 250, 360, 180

if not HEADLESS:
    cap = cv2.VideoCapture(CAMERA_INDEX)
else:
    cap = None  # No camera

def send_status_to_server(spot_id, status):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_HOST, SERVER_PORT))
            message = {
                "action": "update_parking_spot",
                "spot_id": spot_id,
                "status": status
            }
            plaintext = json.dumps(message).encode("utf-8")
            encrypted = cipher.aes_encrypt(plaintext)
            s.send(encrypted)

            encrypted_response = s.recv(1024)
            decrypted_response = cipher.aes_decrypt(encrypted_response)
            response = json.loads(decrypted_response)
            print(f"🔁 Server response: {response}")

    except Exception as e:
        print(f"⚠️ Failed to contact server: {e}")

while True:
    if HEADLESS:
        # Simulate or default to status
        simulated_status = "available"
        send_status_to_server(SPOT_ID, simulated_status)
        print(f"✅ Headless mode - status: {simulated_status}")
        import time
        time.sleep(1)
        continue

    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame")
        break

    cropped = frame[CROP_Y:CROP_Y+CROP_H, CROP_X:CROP_X+CROP_W]
    resized = cv2.resize(cropped, (360, 102)) / 255.0
    input_img = np.expand_dims(resized, axis=0)

    prediction = model.predict(input_img)[0][0]
    status = "available" if prediction < 0.5 else "occupied"
    label = "🅿️ EMPTY" if status == "available" else "🚗 OCCUPIED"
    color = (0, 255, 0) if status == "available" else (0, 0, 255)

    cv2.putText(frame, label, (CROP_X, CROP_Y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.rectangle(frame, (CROP_X, CROP_Y), (CROP_X+CROP_W, CROP_Y+CROP_H), color, 2)

    cv2.imshow(f"Spot {SPOT_ID} - Live View", frame)
    # Save the processed frame to a static folder so Flask can read it
    cv2.imwrite('static/camera_feed.jpg', frame)

    send_status_to_server(SPOT_ID, status)

    if cv2.waitKey(1000) & 0xFF == ord('q'):
        break

if cap:
    cap.release()
cv2.destroyAllWindows()
