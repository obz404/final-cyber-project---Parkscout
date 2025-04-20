import tensorflow as tf
import numpy as np
import cv2
import socket
import json
import sys

# --- Configuration ---
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 65432
SPOT_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 1  # Camera spot ID passed via CLI
CAMERA_INDEX = SPOT_ID - 1  # Map spot 1 to camera 0, spot 2 to camera 1, etc.

# Load the trained model
model = tf.keras.models.load_model('ml_model/parking_model.h5')

# Crop settings
CROP_X = 140
CROP_Y = 250
CROP_W = 360
CROP_H = 180

# Open the camera
cap = cv2.VideoCapture(CAMERA_INDEX)

def send_status_to_server(spot_id, status):
    """Send status update to the server via socket."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_HOST, SERVER_PORT))
            message = {
                "action": "update_parking_spot",
                "spot_id": spot_id,
                "status": status
            }
            s.send(json.dumps(message).encode("utf-8"))
            response = json.loads(s.recv(1024).decode("utf-8"))
            print(f"🔁 Server response: {response}")
    except Exception as e:
        print(f"⚠️ Failed to contact server: {e}")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame")
        break

    cropped = frame[CROP_Y:CROP_Y+CROP_H, CROP_X:CROP_X+CROP_W]
    resized = cv2.resize(cropped, (360, 102)) / 255.0
    input_img = np.expand_dims(resized, axis=0)

    # Predict
    prediction = model.predict(input_img)[0][0]
    status = "available" if prediction < 0.5 else "occupied"
    label = "🅿️ EMPTY" if status == "available" else "🚗 OCCUPIED"
    color = (0, 255, 0) if status == "available" else (0, 0, 255)

    # Draw box and label
    cv2.putText(frame, label, (CROP_X, CROP_Y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.rectangle(frame, (CROP_X, CROP_Y), (CROP_X+CROP_W, CROP_Y+CROP_H), color, 2)

    # Show the frame
    cv2.imshow(f"Spot {SPOT_ID} - Live View", frame)

    # Send status update
    send_status_to_server(SPOT_ID, status)

    # Exit with 'q'
    if cv2.waitKey(1000) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
