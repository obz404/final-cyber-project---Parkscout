from flask import Blueprint, render_template, request, redirect, session, url_for, Response
from .models import User, ParkingSpot, ParkingHistory
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from datetime import datetime
import cv2

main = Blueprint('main', __name__)

# Redirect to homepage
@main.route('/')
def index():
    return redirect(url_for('main.home'))

# Homepage: list of current spot availability
@main.route('/home')
def home():
    spots = ParkingSpot.query.all()
    return render_template('home.html', spots=spots)

# Registration
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = request.form.get('is_admin') == 'on'
        if User.query.filter_by(username=username).first():
            return "Username already taken"
        user = User(username=username, password=generate_password_hash(password), is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('main.login'))
    return render_template('register.html')

# Login
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            return redirect(url_for('main.dashboard'))
        return "Invalid credentials"
    return render_template('login.html')

# Dashboard (admin/user view)
@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    spots = ParkingSpot.query.all()
    return render_template('dashboard.html', spots=spots, is_admin=session.get('is_admin'))

# Reserve a spot
@main.route('/reserve/<int:spot_id>', methods=['POST'])
def reserve_spot(spot_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    spot = ParkingSpot.query.get(spot_id)
    if spot and spot.status == 'available':
        spot.status = 'reserved'
        db.session.commit()
        history = ParkingHistory(
            user_id=session['user_id'],
            parking_date=datetime.now().strftime('%Y-%m-%d'),
            parking_time=datetime.now().strftime('%H:%M:%S')
        )
        db.session.add(history)
        db.session.commit()
    return redirect(url_for('main.dashboard'))

# Admin: Update spot manually
@main.route('/update/<int:spot_id>/<string:new_status>', methods=['POST'])
def update_spot(spot_id, new_status):
    if not session.get('is_admin'):
        return "Unauthorized", 403
    spot = ParkingSpot.query.get(spot_id)
    if spot:
        spot.status = new_status
        db.session.commit()
    return redirect(url_for('main.dashboard'))

# Admin: Add new spot
@main.route('/add_spot', methods=['POST'])
def add_spot():
    if not session.get('is_admin'):
        return "Unauthorized", 403
    db.session.add(ParkingSpot(status="available"))
    db.session.commit()
    return redirect(url_for('main.dashboard'))

# User: Parking history
@main.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    records = ParkingHistory.query.filter_by(user_id=session['user_id']).all()
    return render_template('history.html', records=records)

# View for camera page
@main.route('/camera')
def camera_page():
    return render_template('camera.html')

# Live camera stream
@main.route('/video_feed')
def video_feed():
    def generate():
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
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Logout
@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))
