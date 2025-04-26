import socket
import threading
import logging
import json
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, exists
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from concurrent.futures import ThreadPoolExecutor
from aes_cipher import Cipher  # AES encryption module

# AES Configuration
AES_KEY = b'ThisIsASecretKey'
AES_NONCE = b'ThisIsASecretN'
cipher = Cipher(AES_KEY, AES_NONCE)

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# SQLAlchemy Setup
Base = declarative_base()
engine = create_engine("sqlite:///parking.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# Database Models
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    history = relationship("ParkingHistory", back_populates="user")

class ParkingHistory(Base):
    __tablename__ = 'parking_history'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    parking_date = Column(String, nullable=False)
    parking_time = Column(String, nullable=False)
    user = relationship("User", back_populates="history")

class ParkingSpot(Base):
    __tablename__ = 'parking_spots'
    id = Column(Integer, primary_key=True)
    status = Column(String, default="available")

# Initialize Database

def init_database():
    Base.metadata.create_all(engine)

# Helper function to check if message is encrypted

def is_likely_encrypted(data):
    try:
        json.loads(data.decode('utf-8'))
        return False  # valid JSON, not encrypted
    except:
        return True

# Client Handler

def handle_client(sock, addr):
    logging.info(f"[CONNECTED] {addr}")
    session = SessionLocal()

    try:
        while True:
            raw_data = sock.recv(4096)
            if not raw_data:
                break

            try:
                if is_likely_encrypted(raw_data):
                    decrypted_data = cipher.aes_decrypt(raw_data)
                else:
                    decrypted_data = raw_data.decode("utf-8")
                request = json.loads(decrypted_data)
            except Exception as e:
                logging.error(f"[DECRYPTION ERROR] {e}")
                error = json.dumps({"status": "error", "message": "Invalid request."}).encode()
                sock.send(error)
                break

            action = request.get("action")
            response = {}

            if action == "register":
                username, password = request.get("username"), request.get("password")
                if session.query(exists().where(User.username == username)).scalar():
                    response = {"status": "error", "message": "Username already exists"}
                else:
                    user = User(username=username, password=generate_password_hash(password))
                    session.add(user)
                    session.commit()
                    response = {"status": "success", "message": "Registered successfully"}

            elif action == "login":
                username, password = request.get("username"), request.get("password")
                user = session.query(User).filter_by(username=username).first()
                if user and check_password_hash(user.password, password):
                    response = {"status": "success", "message": "Login successful", "user_id": user.id}
                else:
                    response = {"status": "error", "message": "Invalid credentials"}

            elif action == "add_parking_history":
                user_id, date, time = request.get("user_id"), request.get("parking_date"), request.get("parking_time")
                if session.query(User).filter_by(id=user_id).first():
                    session.add(ParkingHistory(user_id=user_id, parking_date=date, parking_time=time))
                    session.commit()
                    response = {"status": "success", "message": "Parking history recorded"}
                else:
                    response = {"status": "error", "message": "User not found"}

            elif action == "get_parking_history":
                user_id = request.get("user_id")
                history = session.query(ParkingHistory).filter_by(user_id=user_id).all()
                if history:
                    response = {"status": "success", "history": [
                        {"parking_date": h.parking_date, "parking_time": h.parking_time} for h in history
                    ]}
                else:
                    response = {"status": "error", "message": "No history found"}

            elif action == "get_parking_spots":
                spots = session.query(ParkingSpot).all()
                response = {"status": "success", "spots": [{"id": s.id, "status": s.status} for s in spots]}

            elif action == "update_spot_status":
                spot_id = request.get("spot_id")
                status = request.get("status")
                spot = session.query(ParkingSpot).filter_by(id=spot_id).first()
                if spot:
                    spot.status = status
                    session.commit()
                    response = {"status": "success", "message": f"Spot {spot_id} updated to {status}."}
                else:
                    response = {"status": "error", "message": "Spot not found."}

            elif action == "update_parking_spot":
                spot_id, new_status = request.get("spot_id"), request.get("status")
                spot = session.query(ParkingSpot).filter_by(id=spot_id).first()
                if spot:
                    spot.status = new_status
                    session.commit()
                    response = {"status": "success", "message": "Spot updated"}
                else:
                    response = {"status": "error", "message": "Spot not found"}

            elif action == "add_parking_spot":
                new_spot = ParkingSpot(status="available")
                session.add(new_spot)
                session.commit()
                response = {"status": "success", "message": f"Spot {new_spot.id} added", "spot_id": new_spot.id}

            elif action == "reserve_spot":
                user_id, spot_id = request.get("user_id"), request.get("spot_id")
                user = session.query(User).filter_by(id=user_id).first()
                spot = session.query(ParkingSpot).filter_by(id=spot_id).first()
                if user and spot and spot.status == "available":
                    spot.status = "reserved"
                    session.commit()
                    response = {"status": "success", "message": f"Spot {spot_id} reserved"}
                else:
                    response = {"status": "error", "message": "Cannot reserve spot"}

            else:
                response = {"status": "error", "message": "Invalid action"}

            response_bytes = json.dumps(response).encode("utf-8")
            try:
                sock.send(cipher.aes_encrypt(response_bytes))
            except:
                sock.send(response_bytes)

    except Exception as e:
        logging.error(f"[ERROR] {e}")
    finally:
        sock.close()
        session.close()
        logging.info(f"[DISCONNECTED] {addr}")

# Server Starter

def start_server(host="127.0.0.1", port=65432):
    init_database()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    logging.info(f"[LISTENING] Server started on {host}:{port}")
    executor = ThreadPoolExecutor(max_workers=10)
    try:
        while True:
            client_sock, addr = server.accept()
            executor.submit(handle_client, client_sock, addr)
    except KeyboardInterrupt:
        logging.info("[SHUTDOWN] Server shutting down...")
        server.close()

if __name__ == "__main__":
    start_server()