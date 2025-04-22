from flask import Blueprint, render_template, request, redirect, session, url_for
from .models import User, ParkingSpot
from werkzeug.security import check_password_hash
from .app import db

# Create a Blueprint
app = Blueprint('main', __name__)

@app.route('/')
def index():
    return redirect(url_for('main.login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            return redirect(url_for('main.dashboard'))
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    spots = ParkingSpot.query.all()
    return render_template('dashboard.html', spots=spots, is_admin=session.get('is_admin'))

@app.route('/update/<int:spot_id>/<string:new_status>', methods=['POST'])
def update_spot(spot_id, new_status):
    if not session.get('is_admin'):
        return "Unauthorized", 403
    spot = ParkingSpot.query.get(spot_id)
    if spot:
        spot.status = new_status
        db.session.commit()
    return redirect(url_for('main.dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))
