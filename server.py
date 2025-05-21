import socket
import threading
import logging
import json
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, exists
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from concurrent.futures import ThreadPoolExecutor
from aes_cipher import Cipher  # AES encryption module
from datetime import datetime
import base64
import os

# AES Configuration
AES_KEY = b'ThisIsASecretKey'
AES_NONCE = b'ThisIsASecretN'

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# SQLAlchemy base class for declarative models
Base = declarative_base()

class User(Base):
    """
    Represents a user in the parking system.

    Attributes:
        id (int): Primary key.
        username (str): Unique username.
        password (str): Hashed password.
        is_admin (int): 1 if user is admin, 0 otherwise.
        history (List[ParkingHistory]): Related parking history entries.
    """
    __tablename__ = 'users'

    id       = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_admin = Column(Integer, default=0)
    history  = relationship("ParkingHistory", back_populates="user")

class ParkingHistory(Base):
    """
    Records each parking reservation made by a user.

    Attributes:
        id (int): Primary key.
        user_id (int): Foreign key to User.id.
        parking_date (str): Date of reservation (YYYY-MM-DD).
        parking_time (str): Time of reservation (HH:MM:SS).
        spot_id (int): ID of the reserved parking spot.
        user (User): Back-reference to the User.
    """
    __tablename__ = 'parking_history'

    id            = Column(Integer, primary_key=True)
    user_id       = Column(Integer, ForeignKey('users.id'))
    parking_date  = Column(String, nullable=False)
    parking_time  = Column(String, nullable=False)
    spot_id       = Column(Integer, nullable=True)
    user          = relationship("User", back_populates="history")

class ParkingSpot(Base):
    """
    Represents a parking spot in the system.

    Attributes:
        id (int): Primary key.
        status (str): 'available', 'reserved', etc.
    """
    __tablename__ = 'parking_spots'

    id     = Column(Integer, primary_key=True)
    status = Column(String, default="available")

class ParkingServer:
    """
    A socket-based server for managing parking spots, reservations, and history,
    with optional AES encryption for client-server communication.

    Methods:
        init_database: Create DB tables if they don't exist.
        start:          Begin listening for client connections.
        shutdown:       Gracefully close server.
    """

    def __init__(self, host="127.0.0.1", port=65432, max_workers=10, db_url="sqlite:///parking.db"):
        """
        Initialize server settings, AES cipher, DB engine, and thread pool.

        Args:
            host (str): IP address to bind.
            port (int): Port number to listen on.
            max_workers (int): Max threads for client handlers.
            db_url (str): SQLAlchemy DB connection URL.
        """
        self.host = host
        self.port = port
        self.cipher = Cipher(AES_KEY, AES_NONCE)
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.server_socket = None

    def init_database(self):
        """Create all tables defined on Base if not already present."""
        Base.metadata.create_all(self.engine)

    @staticmethod
    def _is_likely_encrypted(raw: bytes) -> bool:
        """
        Heuristic to guess if data is encrypted (non-JSON).

        Args:
            raw (bytes): Raw payload from socket.

        Returns:
            bool: True if payload is probably encrypted.
        """
        try:
            json.loads(raw.decode("utf-8"))
            return False
        except:
            return True

    def handle_client(self, sock: socket.socket, addr):
        """
        Main loop for handling a single client: receive, decrypt, dispatch, and respond.

        Args:
            sock (socket.socket): Connected client socket.
            addr (tuple): Client address.
        """
        logging.info(f"[CONNECTED] {addr}")
        session = self.SessionLocal()
        try:
            while True:
                raw_data = sock.recv(4096)
                if not raw_data:
                    break

                # Attempt decryption if necessary
                try:
                    if self._is_likely_encrypted(raw_data):
                        decrypted = self.cipher.aes_decrypt(raw_data)
                    else:
                        decrypted = raw_data.decode("utf-8")
                    request = json.loads(decrypted)
                except Exception as e:
                    logging.error(f"[DECRYPTION ERROR] {e}")
                    sock.send(json.dumps({"status":"error","message":"Invalid request"}).encode())
                    break

                # Route the action and prepare response
                action = request.get("action")
                response = self.dispatch_action(action, request, session)

                # Encrypt response if client expects encrypted channel
                out = json.dumps(response).encode("utf-8")
                try:
                    encrypted_out = self.cipher.aes_encrypt(out)
                    length = len(encrypted_out)
                    sock.sendall(length.to_bytes(4, byteorder='big'))  # Send 4-byte header
                    sock.sendall(encrypted_out)  # Send actual encrypted message

                except:
                    sock.send(out)

        except Exception as e:
            logging.error(f"[ERROR] {e}")
        finally:
            sock.close()
            session.close()
            logging.info(f"[DISCONNECTED] {addr}")

    def dispatch_action(self, action, request, session):
        """
        Map an action string to the corresponding handler method.

        Args:
            action (str): Name of the requested action.
            request (dict): Parsed JSON payload.
            session (Session): SQLAlchemy DB session.

        Returns:
            dict: Response payload.
        """
        mapping = {
            "register": self._register,
            "login": self._login,
            "add_parking_history": self._add_history,
            "get_parking_history": self._get_history,
            "get_parking_spots": lambda req, sess: self._list_spots(sess),
            "update_spot_status": self._update_spot,
            "add_parking_spot": lambda req, sess: self._add_spot(sess),
            "reserve_spot": self._reserve_spot,
            "remove_parking_spot": self._remove_spot,
            "get_camera_image": self._get_camera_image,

        }
        handler = mapping.get(action)
        if handler:
            return handler(request, session)
        return {"status": "error", "message": "Invalid action"}

    def _register(self, req, session):
        """
        Create a new user account.

        Expects:
            req['username'], req['password'], optional req['is_admin'].

        Returns:
            dict: Success or error message.
        """
        username = req.get("username")
        password = req.get("password")
        is_admin = req.get("is_admin", False)
        # Check uniqueness
        if session.query(exists().where(User.username == username)).scalar():
            return {"status":"error","message":"Username already exists"}
        # Create user
        user = User(
            username=username,
            password=generate_password_hash(password),
            is_admin=1 if is_admin else 0
        )
        session.add(user)
        session.commit()
        return {"status":"success","message":"Registered successfully"}

    def _login(self, req, session):
        """
        Authenticate a user.

        Expects:
            req['username'], req['password'].

        Returns:
            dict: Login result, including user_id and is_admin flag.
        """
        username = req.get("username")
        password = req.get("password")
        user = session.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            return {
                "status":"success",
                "message":"Login successful",
                "user_id": user.id,
                "is_admin": bool(user.is_admin)
            }
        return {"status":"error","message":"Invalid credentials"}

    def _add_history(self, req, session):
        """
        Record a manual parking history entry for a user.

        Expects:
            req['user_id'], req['parking_date'], req['parking_time'].

        Returns:
            dict: Success or error message.
        """
        user_id = req.get("user_id")
        date, time = req.get("parking_date"), req.get("parking_time")
        if session.query(User).filter_by(id=user_id).first():
            session.add(ParkingHistory(
                user_id=user_id,
                parking_date=date,
                parking_time=time
            ))
            session.commit()
            return {"status":"success","message":"Parking history recorded"}
        return {"status":"error","message":"User not found"}

    def _get_history(self, req, session):
        """
        Fetch all parking history entries for a user.

        Expects:
            req['user_id'].

        Returns:
            dict: List of history entries or error.
        """
        user_id = req.get("user_id")
        entries = session.query(ParkingHistory).filter_by(user_id=user_id).all()
        if not entries:
            return {"status":"error","message":"No history found"}
        return {
            "status":"success",
            "history":[
                {
                    "parking_date": e.parking_date,
                    "parking_time": e.parking_time,
                    "spot_id": e.spot_id,
                    "action": "Reserved"
                } for e in entries
            ]
        }

    def _get_camera_image(self, req, session):
        spot_id = req.get("spot_id")
        file_path = os.path.join(os.path.dirname(__file__), "static", f"camera_feed_{spot_id}.jpg")
        print(f"🖼️ Trying to load image from: {file_path}")
        print("📂 Exists?", os.path.exists(file_path))
        try:
            with open(file_path, "rb") as img_file:
                img_bytes = img_file.read()
                img_b64 = base64.b64encode(img_bytes).decode('utf-8')
                return {
                    "status": "success",
                    "image": img_b64
                }
        except FileNotFoundError:
            return {"status": "error", "message": "Image not found"}

    def _list_spots(self, session):
        """
        List all parking spots with their current status.

        Returns:
            dict: List of spot IDs and statuses.
        """
        spots = session.query(ParkingSpot).all()
        return {
            "status": "success",
            "spots": [{"id": s.id, "status": s.status} for s in spots]
        }

    def _update_spot(self, req, session):
        """
        Update the status of a specific spot.

        Expects:
            req['spot_id'], req['status'].

        Returns:
            dict: Success or error message.
        """
        spot = session.get(ParkingSpot, req.get("spot_id"))

        if not spot:
            return {"status":"error","message":"Spot not found"}
        spot.status = req.get("status")
        session.commit()
        return {"status":"success","message":f"Spot {spot.id} updated to {spot.status}."}

    def _add_spot(self, session):
        """
        Create a new parking spot record.

        Returns:
            dict: New spot ID.
        """
        new_spot = ParkingSpot()
        session.add(new_spot)
        session.commit()
        return {
            "status":"success",
            "message":f"Spot {new_spot.id} added",
            "spot_id": new_spot.id
        }

    def _reserve_spot(self, req, session):
        """
        Reserve an available spot for a user and record history.

        Expects:
            req['user_id'], req['spot_id'].

        Returns:
            dict: Success or error.
        """
        user = session.get(User, req.get("user_id"))
        spot = session.get(ParkingSpot, req.get("spot_id"))

        if user and spot and spot.status == "available":
            spot.status = "reserved"
            now = datetime.now()
            session.add(ParkingHistory(
                user_id=user.id,
                parking_date=now.strftime("%Y-%m-%d"),
                parking_time=now.strftime("%H:%M:%S"),
                spot_id=spot.id
            ))
            session.commit()
            return {"status":"success","message":f"Spot {spot.id} reserved"}
        return {"status":"error","message":"Cannot reserve spot"}

    def _remove_spot(self, req, session):
        """
        Delete a parking spot record.

        Expects:
            req['spot_id'].

        Returns:
            dict: Success or error message.
        """
        spot = session.get(ParkingSpot, req.get("spot_id"))

        if not spot:
            return {"status":"error","message":"Spot not found"}
        session.delete(spot)
        session.commit()
        return {"status":"success","message":f"Spot {spot.id} removed"}

    def start(self):
        """
        Initialize DB, bind socket, and enter accept loop to handle clients.
        """
        self.init_database()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        logging.info(f"[LISTENING] Server running on {self.host}:{self.port}")

        try:
            while True:
                client_sock, addr = self.server_socket.accept()
                # Submit each client handler to the thread pool
                self.executor.submit(self.handle_client, client_sock, addr)
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        """
        Gracefully shut down the server and thread pool.
        """
        logging.info("[SHUTDOWN] Server is shutting down")
        if self.server_socket:
            self.server_socket.close()
        self.executor.shutdown(wait=False)


if __name__ == "__main__":
    # Entry point: start the parking server
    server = ParkingServer(host="0.0.0.0", port=65432, max_workers=10)
    server.start()
