"""
camera_predict.py

Continuously captures frames from a camera (or simulates in headless mode),
runs a TensorFlow model to classify a parking spot as empty or occupied,
and updates the central ParkingServer via AES-encrypted socket messages.
Also saves annotated frames and status JSON files for the Flask UI.

Usage:
    python camera_predict.py [SPOT_ID] [CAMERA_INDEX] [--headless]

Args:
    SPOT_ID (int, optional): ID of the parking spot to monitor (default: 1).
    CAMERA_INDEX (int, optional): OpenCV camera index (default: SPOT_ID - 1).
    --headless: Run without camera; simulate 'available' every 5 seconds.

Outputs:
    - static/status_<SPOT_ID>.json      : Latest status JSON for web UI
    - static/camera_feed_<SPOT_ID>.jpg  : Annotated latest camera frame
"""

import tensorflow as tf
import numpy as np
import cv2
import socket
import json
import sys
import os
import time
from aes_cipher import Cipher

# -------------------------------------------------------------------
# Configuration and Globals
# -------------------------------------------------------------------

# Server connection settings (must match ParkingServer)
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 65432

# AES encryption parameters (must match server)
AES_KEY = b'ThisIsASecretKey'
AES_NONCE = b'ThisIsASecretN'
cipher = Cipher(AES_KEY, AES_NONCE)

# Command-line arguments
SPOT_ID      = int(sys.argv[1]) if len(sys.argv) > 1 else 1
CAMERA_INDEX = int(sys.argv[2]) if len(sys.argv) > 2 else SPOT_ID - 1
HEADLESS     = "--headless" in sys.argv

# TensorFlow model path
MODEL_PATH = 'ml_model/parking_model.h5'

# Region-of-Interest for cropping: (x, y, width, height)
CROP_X, CROP_Y, CROP_W, CROP_H = 140, 250, 360, 180

# Shared socket for communication with the server
camera_sock = None

# -------------------------------------------------------------------
# Initialization
# -------------------------------------------------------------------

def init_camera_socket():
    """
    Initialize a persistent AES-encrypted socket connection to the ParkingServer.
    Reuses the same socket for multiple requests.
    """
    global camera_sock
    if camera_sock is None:
        camera_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        camera_sock.connect((SERVER_HOST, SERVER_PORT))

# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------

def get_current_status(spot_id):
    """
    Query the server for the current status of all spots,
    then return the status string for the given spot_id.

    Args:
        spot_id (int): ID of the parking spot to query.

    Returns:
        str or None: 'available', 'occupied', 'reserved', or None on error.
    """
    global camera_sock
    try:
        init_camera_socket()
        request = {"action": "get_parking_spots"}
        payload = json.dumps(request).encode("utf-8")
        camera_sock.sendall(cipher.aes_encrypt(payload))

        # Read 4-byte length prefix
        raw_len = camera_sock.recv(4)
        if len(raw_len) < 4:
            raise ValueError("Incomplete length prefix")
        msg_len = int.from_bytes(raw_len, byteorder='big')

        # Now receive the full encrypted response
        encrypted_resp = b""
        while len(encrypted_resp) < msg_len:
            chunk = camera_sock.recv(min(4096, msg_len - len(encrypted_resp)))
            if not chunk:
                break
            encrypted_resp += chunk

        # Decrypt
        decrypted_resp = cipher.aes_decrypt(encrypted_resp)

        data = json.loads(decrypted_resp)

        for spot in data.get("spots", []):
            if spot["id"] == spot_id:
                return spot["status"]
    except Exception:
        # Reset socket on any failure to force reconnection next call
        try:
            camera_sock.close()
        except:
            pass
        camera_sock = None
    return None

def send_status_to_server(spot_id, status):
    """
    Send an update to the server with this spot's new status.

    Args:
        spot_id (int): ID of the parking spot being updated.
        status (str): New status ('available', 'occupied', 'reserved').
    """
    global camera_sock
    try:
        init_camera_socket()
        message = {
            "action":  "update_spot_status",
            "spot_id": spot_id,
            "status":  status
        }
        payload = json.dumps(message).encode("utf-8")
        camera_sock.sendall(cipher.aes_encrypt(payload))

        # Read 4-byte length prefix
        raw_len = camera_sock.recv(4)
        if len(raw_len) < 4:
            raise ValueError("Incomplete length prefix")
        msg_len = int.from_bytes(raw_len, byteorder='big')

        # Now receive the full encrypted response
        encrypted_resp = b""
        while len(encrypted_resp) < msg_len:
            chunk = camera_sock.recv(min(4096, msg_len - len(encrypted_resp)))
            if not chunk:
                break
            encrypted_resp += chunk

        # Decrypt
        decrypted_resp = cipher.aes_decrypt(encrypted_resp)

        response = json.loads(decrypted_resp)
        print(f"🔁 Server response: {response}")
    except Exception as e:
        print(f"⚠️ Failed to contact server: {e}")
        # Reset socket to reconnect on next attempt
        try:
            camera_sock.close()
        except:
            pass
        camera_sock = None

def save_status_locally(spot_id, status):
    """
    Persist the latest status to a JSON file under 'static/' for the web UI.

    Args:
        spot_id (int): Parking spot ID.
        status (str): Current status.
    """
    os.makedirs('static', exist_ok=True)
    status_data = {"spot_id": spot_id, "status": status}
    with open(f'static/status_{spot_id}.json', 'w') as f:
        json.dump(status_data, f)

# -------------------------------------------------------------------
# Main Loop
# -------------------------------------------------------------------

def main():
    """
    Load the model, open the camera (unless headless), and enter the
    continuous loop to predict status, annotate frames, and update server/UI.
    """
    # Load the trained TensorFlow model
    model = tf.keras.models.load_model(MODEL_PATH)

    # Initialize OpenCV video capture if not headless
    cap = None
    if not HEADLESS:
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            print(f"❌ Camera {CAMERA_INDEX} not found. Marking Spot {SPOT_ID} as occupied.")
            send_status_to_server(SPOT_ID, "occupied")
            save_status_locally(SPOT_ID, "occupied")
            return

    print(f"▶️ Starting camera_predict for Spot {SPOT_ID} "
          f"(Camera {CAMERA_INDEX}, Headless={HEADLESS})")

    try:
        while True:
            if HEADLESS:
                # Simulate available status in headless mode every 5 seconds
                simulated = "available"
                send_status_to_server(SPOT_ID, simulated)
                save_status_locally(SPOT_ID, simulated)
                print(f"✅ Headless: Spot {SPOT_ID} -> {simulated}")
                time.sleep(5)
                continue

            # Capture a frame
            ret, frame = cap.read()
            if not ret:
                print(f"⚠️ Failed to grab frame for Spot {SPOT_ID}. Retrying...")
                time.sleep(1)
                continue

            # Crop ROI and preprocess for model
            roi = frame[CROP_Y:CROP_Y + CROP_H, CROP_X:CROP_X + CROP_W]
            resized = cv2.resize(roi, (360, 102)) / 255.0
            input_img = np.expand_dims(resized, axis=0)

            # Predict occupancy (model outputs a single sigmoid score)
            score = model.predict(input_img, verbose=0)[0][0]
            predicted = "available" if score < 0.5 else "occupied"

            # Preserve 'reserved' state unless a car is detected
            current = get_current_status(SPOT_ID)
            if current == "reserved":
                status = "reserved" if predicted == "available" else "occupied"
            else:
                status = predicted

            # Choose label text and box color
            if status == "reserved":
                label = "🅿️ RESERVED";  color = (160, 32, 240)
            elif status == "occupied":
                label = "🚗 OCCUPIED";   color = (0, 0, 255)
            else:
                label = "🅿️ EMPTY";      color = (0, 255, 0)

            # Annotate frame: label above ROI and colored rectangle
            cv2.putText(frame, label,
                        (CROP_X, CROP_Y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1, color, 2)
            cv2.rectangle(frame,
                          (CROP_X, CROP_Y),
                          (CROP_X + CROP_W, CROP_Y + CROP_H),
                          color, 2)

            # Ensure UI folder and save annotated frame + update server/UI
            os.makedirs('static', exist_ok=True)
            cv2.imwrite(f'static/camera_feed_{SPOT_ID}.jpg', frame)

            send_status_to_server(SPOT_ID, status)
            save_status_locally(SPOT_ID, status)

            # Display live window; press 'q' to quit
            cv2.imshow(f"Spot {SPOT_ID}", frame)
            if cv2.waitKey(1000) & 0xFF == ord('q'):
                print("🛑 Quitting camera loop.")
                break

    finally:
        # Clean up resources
        if cap:
            cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
