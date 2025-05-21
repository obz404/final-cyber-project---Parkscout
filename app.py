"""
app.py

Flask web interface for the ParkScout parking system.

Provides:
  - User authentication (register, login, logout)
  - Viewing and reserving parking spots
  - Viewing parking history
  - Admin dashboard for adding/removing spots
  - Live camera feed and status endpoints for integration with camera_predict.py

Note:
  This is the main Flask application that interacts with a backend ParkingServer
  over an AES-encrypted TCP socket, and serves HTML templates and JSON APIs.
"""

import socket
import json
import os
from functools import wraps
from datetime import datetime
from flask import send_file
from io import BytesIO
import base64

import cv2
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, Response
)
from aes_cipher import Cipher

# -------------------------------------------------------------------
# Module-level socket for reuse across requests
# -------------------------------------------------------------------
client_sock = None

def init_client_socket():
    """
    Initialize or reuse a single TCP socket to the ParkingServer.
    Ensures only one connection is open per application instance.
    """
    global client_sock
    if client_sock is None:
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.connect((SERVER_HOST, SERVER_PORT))

# -------------------------------------------------------------------
# Hardcoded admin credentials (username: password)
# -------------------------------------------------------------------
ADMIN_CREDENTIALS = {
    "admin1":   "adminpass123",
    "obz404":   "obzsecure!",
    "manager":  "letmein456"
}

# -------------------------------------------------------------------
# Flask app configuration
# -------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

# -------------------------------------------------------------------
# AES Encryption Setup (must match server settings)
# -------------------------------------------------------------------
AES_KEY   = b'ThisIsASecretKey'
AES_NONCE = b'ThisIsASecretN'
cipher    = Cipher(AES_KEY, AES_NONCE)

# -------------------------------------------------------------------
# ParkingServer connection settings
# -------------------------------------------------------------------
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 65432

# =================== Utility Functions ===================

def send_request(action, data=None):
    """
    Send an AES-encrypted JSON request to the ParkingServer and return its response.

    Args:
        action (str): Name of the backend action (e.g., 'login', 'get_parking_spots').
        data (dict, optional): Additional payload data for the action.

    Returns:
        dict: Parsed JSON response from the server, or an error dict on failure.
    """
    global client_sock
    if data is None:
        data = {}

    try:
        init_client_socket()
        # Build and encrypt request payload
        payload = json.dumps({"action": action, **data}).encode("utf-8")
        encrypted = cipher.aes_encrypt(payload)
        client_sock.sendall(encrypted)

        # Receive and decrypt response
        encrypted_resp = b""
        while True:
            chunk = client_sock.recv(4096)
            if not chunk:
                break
            encrypted_resp += chunk
            if len(chunk) < 4096:
                break

        decrypted = cipher.aes_decrypt(encrypted_resp)
        return json.loads(decrypted)

    except Exception as e:
        # On any socket error, reset connection for next time
        try:
            client_sock.close()
        except:
            pass
        client_sock = None
        return {"status": "error", "message": str(e)}

def login_required(f):
    """
    Decorator to protect routes that require a logged-in user.
    Redirects to login page with a flash message if not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorator to protect routes that require admin privileges.
    Redirects to home page with a flash message if not authorized.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin', False):
            flash("Admin access required.", "danger")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# =================== Route Definitions ===================

@app.route('/')
def index():
    """Root route: redirect to login page."""
    return redirect(url_for('login'))

# --------- Authentication ---------

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login and registration.

    - POST with action='register' attempts to create a new account.
    - POST with action='login' attempts to authenticate an existing user.
    On success, stores user_id, username, and is_admin in session.
    """
    if request.method == 'POST':
        action   = request.form.get('action')
        username = request.form['username']
        password = request.form['password']

        if action == 'register':
            # Determine admin flag based on hardcoded credentials
            is_admin = (username in ADMIN_CREDENTIALS
                        and ADMIN_CREDENTIALS[username] == password)
            response = send_request('register', {
                "username": username,
                "password": password,
                "is_admin": is_admin
            })
            if response.get("status") == "success":
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for('login'))
            else:
                flash(response.get("message", "Registration failed."), "danger")

        elif action == 'login':
            # Attempt backend authentication
            response = send_request('login', {
                "username": username,
                "password": password
            })
            if response.get("status") == "success":
                # Store session info
                session['user_id']  = response['user_id']
                session['username'] = username
                session['is_admin'] = response.get('is_admin', False)
                return redirect(url_for('home'))
            else:
                flash(response.get("message", "Login failed."), "danger")

    # GET request or failed POST falls through to render login form
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Log out the current user by clearing the session."""
    session.clear()
    return redirect(url_for('login'))

# --------- User Views ---------

@app.route('/home')
@login_required
def home():
    """
    Display the user home page with a list of parking spots.
    Fetches current spot statuses from the backend.
    """
    response = send_request('get_parking_spots')
    spots = response.get('spots', []) if response.get('status') == 'success' else []
    return render_template('home.html', spots=spots)

@app.route('/reserve/<int:spot_id>', methods=['POST'])
@login_required
def reserve(spot_id):
    """
    Reserve a parking spot for the logged-in user.
    Sends reserve_spot request to backend and flashes success/failure.
    """
    response = send_request('reserve_spot', {
        "user_id": session['user_id'],
        "spot_id": spot_id
    })
    if response.get('status') == 'success':
        # Record reservation time for UI feedback
        now = datetime.now()
        flash(f"Spot {spot_id} reserved at {now.strftime('%Y-%m-%d %H:%M:%S')}.", "success")
    else:
        flash(response.get("message", "Failed to reserve spot."), "danger")
    return redirect(url_for('home'))

@app.route('/history')
@login_required
def history():
    """
    Show the parking history for the logged-in user.
    Retrieves history entries from the backend.
    """
    response = send_request('get_parking_history', {
        "user_id": session['user_id']
    })
    records = response.get('history', []) if response.get('status') == 'success' else []
    return render_template('history.html', records=records)

# --------- Admin Views ---------

@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    """
    Admin dashboard displaying all parking spots.
    Allows adding or removing spots.
    """
    response = send_request('get_parking_spots')
    spots = response.get('spots', []) if response.get('status') == 'success' else []
    return render_template('admin_dashboard.html', spots=spots)

@app.route('/add_spot', methods=['POST'])
@login_required
@admin_required
def add_spot():
    """Add a new parking spot via the backend."""
    response = send_request('add_parking_spot')
    if response.get('status') == 'success':
        flash("Parking spot added.", "success")
    else:
        flash("Failed to add parking spot.", "danger")
    return redirect(url_for('admin_dashboard'))

@app.route('/remove_spot/<int:spot_id>', methods=['POST'])
@login_required
@admin_required
def remove_spot(spot_id):
    """Remove a parking spot via the backend."""
    response = send_request('remove_parking_spot', {"spot_id": spot_id})
    if response.get('status') == 'success':
        flash(f"Spot {spot_id} removed.", "success")
    else:
        flash(response.get("message", "Failed to remove spot."), "danger")
    return redirect(url_for('admin_dashboard'))

# --------- Camera & API Endpoints ---------

@app.route('/status/<int:spot_id>')
@login_required
def status(spot_id):
    """
    Return the latest status JSON for a given spot_id.
    Reads from the static/status_<spot_id>.json file written by camera_predict.py.
    """
    try:
        with open(f'static/status_{spot_id}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"status": "unknown"}

@app.route('/camera')
@login_required
def camera():
    """
    Render the camera view page with dynamic list of spot IDs.
    """
    response = send_request('get_parking_spots')
    spot_ids = [spot['id'] for spot in response.get('spots', [])] if response.get('status') == 'success' else []
    return render_template('camera.html', spot_ids=spot_ids)

@app.route('/api/parking_spots')
@login_required
def api_parking_spots():
    """
    JSON API endpoint returning all parking spot statuses.
    Useful for AJAX calls from the front-end.
    """
    return send_request('get_parking_spots')

@app.route('/video_feed')
def video_feed():
    """
    Streaming endpoint for live camera frames.
    Uses multipart/x-mixed-replace to serve JPEG frames.
    """
    return Response(
        generate_camera_feed(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
@app.route('/camera_image/<int:spot_id>')
@login_required
def camera_image(spot_id):
    response = send_request('get_camera_image', {"spot_id": spot_id})
    if response.get("status") == "success":
        image_b64 = response["image"]
        image_bytes = base64.b64decode(image_b64)
        return send_file(BytesIO(image_bytes), mimetype='image/jpeg')
    else:
        return "Image not found", 404

def generate_camera_feed():
    """
    Generator function that captures frames from the default camera
    and yields them as JPEG frames for the video_feed endpoint.
    """
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
        )
    cap.release()

# =================== Application Entry Point ===================

if __name__ == '__main__':
    """
    Run the Flask development server.
    Set debug=False in production.
    """
    app.run(debug=True)
