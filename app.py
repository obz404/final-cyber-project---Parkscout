from flask import Flask, render_template, request, redirect, session, url_for, flash, Response
import socket
import json
from aes_cipher import Cipher
from functools import wraps
import cv2

app = Flask(__name__)
app.secret_key = "supersecretkey"

# AES Encryption Setup
AES_KEY = b'ThisIsASecretKey'
AES_NONCE = b'ThisIsASecretN'
cipher = Cipher(AES_KEY, AES_NONCE)

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 65432

# =================== Utilities ===================

def send_request(action, data={}):
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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash("Admin access required.", "danger")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# =================== Routes ===================

@app.route('/')
def index():
    return redirect(url_for('login'))

# --------- Authentication ---------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form['username']
        password = request.form['password']

        if action == 'register':
            is_admin = 'is_admin' in request.form
            response = send_request('register', {
                "username": username,
                "password": password,
                "is_admin": is_admin
            })
            if response["status"] == "success":
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for('login'))
            else:
                flash(response.get("message", "Registration failed"), "danger")

        elif action == 'login':
            response = send_request('login', {"username": username, "password": password})
            if response["status"] == "success":
                session['user_id'] = response['user_id']
                session['username'] = username
                session['is_admin'] = response.get('is_admin', False)
                return redirect(url_for('home'))
            else:
                flash(response.get("message", "Login failed"), "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --------- User Views ---------

@app.route('/home')
@login_required
def home():
    response = send_request('get_parking_spots')
    spots = response.get('spots', []) if response['status'] == 'success' else []
    return render_template('home.html', spots=spots)

@app.route('/reserve/<int:spot_id>', methods=['POST'])
@login_required
def reserve(spot_id):
    response = send_request('reserve_spot', {"user_id": session['user_id'], "spot_id": spot_id})
    if response['status'] == 'success':
        flash('Spot reserved successfully!', 'success')
    else:
        flash(response.get('message', 'Failed to reserve spot.'), 'danger')
    return redirect(url_for('home'))

@app.route('/history')
@login_required
def history():
    response = send_request('get_parking_history', {"user_id": session['user_id']})
    records = response.get('history', []) if response['status'] == 'success' else []
    return render_template('history.html', records=records)

# --------- Admin Views ---------

@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    response = send_request('get_parking_spots')
    spots = response.get('spots', []) if response['status'] == 'success' else []
    return render_template('admin_dashboard.html', spots=spots)

@app.route('/add_spot', methods=['POST'])
@login_required
@admin_required
def add_spot():
    response = send_request('add_parking_spot')
    if response['status'] == 'success':
        flash('Parking spot added.', 'success')
    else:
        flash('Failed to add parking spot.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/remove_spot/<int:spot_id>', methods=['POST'])
@login_required
@admin_required
def remove_spot(spot_id):
    response = send_request('remove_parking_spot', {"spot_id": spot_id})
    if response['status'] == 'success':
        flash('Spot removed successfully.', 'success')
    else:
        flash(response.get('message', 'Failed to remove spot.'), 'danger')
    return redirect(url_for('admin_dashboard'))

# --------- Camera Views ---------
@app.route('/status/<int:spot_id>')
@login_required
def status(spot_id):
    try:
        with open(f'static/status_{spot_id}.json', 'r') as f:
            status_data = json.load(f)
        return status_data
    except:
        return {"status": "unknown"}

@app.route('/camera')
@login_required
def camera():
    return render_template('camera.html')

@app.route('/api/parking_spots')
@login_required
def api_parking_spots():
    response = send_request('get_parking_spots')
    return response

@app.route('/video_feed')
def video_feed():
    return Response(generate_camera_feed(), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_camera_feed():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    cap.release()

# =================== Main ===================

if __name__ == '__main__':
    app.run(debug=True)
