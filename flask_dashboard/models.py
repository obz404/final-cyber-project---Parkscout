from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    spots = db.relationship("ParkingSpot", backref="user", lazy=True)
    history = db.relationship("ParkingHistory", backref="user", lazy=True)

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String, default="available")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

class ParkingHistory(db.Model):
    __tablename__ = 'parking_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    parking_date = db.Column(db.String, nullable=False)
    parking_time = db.Column(db.String, nullable=False)