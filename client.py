"""
client.py

A simple terminal-based test client for the ParkScout parking system.
This script runs in the console and serves as a preliminary client
before the full Flask-based web interface is implemented.

Usage:
    python client.py
"""

import socket
import json

# Server connection settings
SERVER_HOST = "127.0.0.1"  # Change if server runs on a different host
SERVER_PORT = 65432        # Must match the ParkingServer port

def send_request(action, data=None):
    """
    Send a JSON request to the ParkingServer and receive its response.

    Args:
        action (str): The action name (e.g., "register", "login", etc.).
        data (dict, optional): Additional parameters for the action.

    Returns:
        dict: Parsed JSON response from the server, or error information.
    """
    payload = {"action": action}
    if data:
        payload.update(data)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            client_socket.send(json.dumps(payload).encode("utf-8"))
            raw = client_socket.recv(4096).decode("utf-8")
            return json.loads(raw)
    except Exception as e:
        return {"status": "error", "message": str(e)}

def register():
    """Prompt for username/password and register a new user with the server."""
    username = input("Enter username: ")
    password = input("Enter password: ")
    response = send_request("register", {"username": username, "password": password})
    print(response.get("message", "No response"))

def login():
    """
    Prompt for username/password and attempt to log in.
    Returns the user_id on success, or None on failure.
    """
    username = input("Enter username: ")
    password = input("Enter password: ")
    response = send_request("login", {"username": username, "password": password})

    if response.get("status") == "success":
        print("Login successful!")
        return response.get("user_id")
    else:
        print(response.get("message", "Login failed"))
        return None

def check_parking_spots():
    """Retrieve and display the list of all parking spots and their status."""
    response = send_request("get_parking_spots")
    if response.get("status") == "success":
        print("\nAvailable Parking Spots:")
        for spot in response.get("spots", []):
            print(f"  • ID: {spot['id']} — Status: {spot['status']}")
    else:
        print("Error:", response.get("message", "Unable to fetch spots"))

def reserve_spot(user_id):
    """
    Prompt the user to choose a spot and send a reservation request.
    Requires a valid logged-in user_id.
    """
    check_parking_spots()
    try:
        spot_id = int(input("\nEnter the ID of the spot to reserve: "))
    except ValueError:
        print("Invalid ID format.")
        return

    response = send_request("reserve_spot", {"user_id": user_id, "spot_id": spot_id})
    print(response.get("message", "No response"))

def check_parking_history(user_id):
    """Fetch and display the parking reservation history for the logged-in user."""
    response = send_request("get_parking_history", {"user_id": user_id})
    if response.get("status") == "success":
        print("\nYour Parking History:")
        for entry in response.get("history", []):
            date = entry.get("parking_date")
            time = entry.get("parking_time")
            spot = entry.get("spot_id", "N/A")
            print(f"  • Date: {date} | Time: {time} | Spot ID: {spot}")
    else:
        print("Error:", response.get("message", "No history found"))

def add_parking_spot():
    """Request the server to create a new parking spot record."""
    response = send_request("add_parking_spot")
    print(response.get("message", "No response"))

def main():
    """
    Main menu loop presenting options to the user.
    Options include registration, login, spot viewing, reservation, history, and exit.
    """
    print("\n🚗 ParkScout Terminal Test Client 🚗")
    user_id = None

    menu = {
        "1": ("Register a new account", register),
        "2": ("Login to existing account", lambda: login()),
        "3": ("View parking spots", check_parking_spots),
        "4": ("Reserve a spot", lambda: reserve_spot(user_id) if user_id else print("Please login first.")),
        "5": ("View parking history", lambda: check_parking_history(user_id) if user_id else print("Please login first.")),
        "6": ("Add a new parking spot", add_parking_spot),
        "7": ("Exit", None)
    }

    while True:
        print("\nMenu:")
        for key, (desc, _) in menu.items():
            print(f"  {key}. {desc}")

        choice = input("Select an option: ").strip()
        if choice == "7":
            print("Goodbye! 👋")
            break

        action = menu.get(choice)
        if not action:
            print("Invalid selection. Try again.")
            continue

        # Execute the chosen function
        func = action[1]
        result = func()
        # Capture user_id when logging in
        if choice == "2" and isinstance(result, int):
            user_id = result

if __name__ == "__main__":
    main()
