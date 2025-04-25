from flask import Flask, render_template, request, redirect, session, url_for, jsonify, Response
import socket
import json
import cv2
import tensorflow as tf
import numpy as np
from aes_cipher import Cipher

# AES Encryption Setup
AES_KEY = b'ThisIsASecretKey'
AES_NONCE = b'ThisIsASecretN'
cipher = Cipher(AES_KEY, AES_NONCE)

# Flask App
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Server Socket Config
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 65432

# Load Prediction Model
model = tf.keras.models.load_model("ml_model/parking_model.h5")
CROP_X, CROP_Y, CROP_W, CROP_H = 140, 250, 360, 180
CAMERA_INDEX = 0

def send_request(action, data={}):
    """Send AES-encrypted request to socket server and decrypt the response."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_HOST, SERVER_PORT))
            payload = json.dumps({"action": action, **data}).encode("utf-8")
            s.send(cipher.aes_encrypt(payload))

            encrypted_response = s.recv(4096)
            decrypted = cipher.aes_decrypt(encrypted_response)
            return json.loads(decrypted)
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "register":
            return jsonify(send_request("register", {
                "username": request.form["username"],
                "password": request.form["password"]
            }))

        if action == "login":
            response = send_request("login", {
                "username": request.form["username"],
                "password": request.form["password"]
            })
            if response["status"] == "success":
                session["user_id"] = response["user_id"]
            return jsonify(response)

        if action == "reserve":
            return jsonify(send_request("reserve_spot", {
                "user_id": session.get("user_id"),
                "spot_id": int(request.form["spot_id"])
            }))

        if action == "add_spot":
            return jsonify(send_request("add_parking_spot"))

        if action == "get_history":
            return jsonify(send_request("get_parking_history", {
                "user_id": session.get("user_id")
            }))

        if action == "get_spots":
            return jsonify(send_request("get_parking_spots"))

    return render_template("index.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/video_feed")
def video_feed():
    def generate():
        cap = cv2.VideoCapture(CAMERA_INDEX)
        while True:
            ret, frame = cap.read()
            if not ret:
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

            _, buffer = cv2.imencode('.jpg', frame)
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

        cap.release()

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    app.run(debug=True)
