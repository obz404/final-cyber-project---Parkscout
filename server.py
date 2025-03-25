import socket
import threading
import logging
import json
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, exists
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from concurrent.futures import ThreadPoolExecutor

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine("sqlite:///parking.db", echo=False, connect_args={"check_same_thread": False}, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(bind=engine)

# Database models
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    parking_history = relationship("ParkingHistory", back_populates="user")

class ParkingHistory(Base):
    __tablename__ = 'parking_history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    parking_date = Column(String, nullable=False)
    parking_time = Column(String, nullable=False)
    user = relationship("User", back_populates="parking_history")

class ParkingSpot(Base):
    __tablename__ = 'parking_spots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String, nullable=False, default="available")

# Initialize the database
def init_database():
    Base.metadata.create_all(engine)

# Handle client requests
def handle_client(client_socket, addr):
    logging.info(f"[NEW CONNECTION] {addr} connected.")
    session = SessionLocal()

    try:
        while True:
            data = client_socket.recv(1024).decode("utf-8")
            if not data:
                break

            request = json.loads(data)
            action = request.get("action")
            response = {}

            if action == "register":
                username = request.get("username")
                password = request.get("password")
                if session.query(exists().where(User.username == username)).scalar():
                    response = {"status": "error", "message": "Username already exists."}
                else:
                    hashed_password = generate_password_hash(password)
                    new_user = User(username=username, password=hashed_password)
                    session.add(new_user)
                    session.commit()
                    response = {"status": "success", "message": "User registered successfully."}

            elif action == "login":
                username = request.get("username")
                password = request.get("password")
                user = session.query(User).filter_by(username=username).first()
                if user and check_password_hash(user.password, password):
                    response = {"status": "success", "message": "Login successful.", "user_id": user.id}
                else:
                    response = {"status": "error", "message": "Invalid credentials."}

            elif action == "add_parking_history":
                user_id = request.get("user_id")
                parking_date = request.get("parking_date")
                parking_time = request.get("parking_time")
                if session.query(exists().where(User.id == user_id)).scalar():
                    new_history = ParkingHistory(user_id=user_id, parking_date=parking_date, parking_time=parking_time)
                    session.add(new_history)
                    session.commit()
                    response = {"status": "success", "message": "Parking history added."}
                else:
                    response = {"status": "error", "message": "User not found."}

            elif action == "get_parking_history":
                user_id = request.get("user_id")
                history = session.query(ParkingHistory).filter_by(user_id=user_id).all()
                history_list = [{"parking_date": h.parking_date, "parking_time": h.parking_time} for h in history]
                response = {"status": "success", "history": history_list} if history_list else {"status": "error", "message": "No history found."}

            elif action == "get_parking_spots":
                spots = session.query(ParkingSpot).all()
                spot_list = [{"id": s.id, "status": s.status} for s in spots]
                response = {"status": "success", "spots": spot_list}

            elif action == "update_parking_spot":
                spot_id = request.get("spot_id")
                new_status = request.get("status")
                spot = session.query(ParkingSpot).filter_by(id=spot_id).first()
                if spot:
                    spot.status = new_status
                    session.commit()
                    response = {"status": "success", "message": "Parking spot updated."}
                else:
                    response = {"status": "error", "message": "Parking spot not found."}

            elif action == "reserve_spot":
                user_id = request.get("user_id")
                spot_id = request.get("spot_id")
                user = session.query(User).filter_by(id=user_id).first()
                spot = session.query(ParkingSpot).filter_by(id=spot_id).first()

            elif action == "add_parking_spot":
                new_spot = ParkingSpot(status="available")
                session.add(new_spot)
                session.commit()
                response = {"status": "success", "message": f"Parking spot {new_spot.id} added.",
                            "spot_id": new_spot.id}

                if user and spot and spot.status == "available":
                    spot.status = "reserved"
                    session.commit()
                    response = {"status": "success", "message": f"Spot {spot_id} reserved."}
                else:
                    response = {"status": "error", "message": "Spot not available or invalid user."}

            else:
                response = {"status": "error", "message": "Invalid action."}

            client_socket.send(json.dumps(response).encode("utf-8"))

    except Exception as e:
        logging.error(f"[ERROR] {e}")
    finally:
        client_socket.close()
        session.close()
        logging.info(f"[DISCONNECT] {addr} disconnected.")

# Start the server
def start_server(host="127.0.0.1", port=65432):
    init_database()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    logging.info(f"[LISTENING] Server is listening on {host}:{port}")

    executor = ThreadPoolExecutor(max_workers=10)

    try:
        while True:
            client_socket, addr = server.accept()
            executor.submit(handle_client, client_socket, addr)
            logging.info(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
    except KeyboardInterrupt:
        logging.info("\n[SHUTDOWN] Server shutting down...")
        server.close()

if __name__ == "__main__":
    start_server()
