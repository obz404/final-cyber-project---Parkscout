import socket
import json

SERVER_HOST = "127.0.0.1"  # Change this if your server is running on a different machine
SERVER_PORT = 65432

def send_request(action, data={}):
    """Send a request to the server and return the response."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            request = {"action": action, **data}
            client_socket.send(json.dumps(request).encode("utf-8"))
            response = json.loads(client_socket.recv(1024).decode("utf-8"))
            return response
        except Exception as e:
            return {"status": "error", "message": str(e)}

def register():
    """Register a new user."""
    username = input("Enter username: ")
    password = input("Enter password: ")
    response = send_request("register", {"username": username, "password": password})
    print(response["message"])

def login():
    """Login an existing user."""
    username = input("Enter username: ")
    password = input("Enter password: ")
    response = send_request("login", {"username": username, "password": password})
    if response["status"] == "success":
        print("Login successful!")
        return response["user_id"]
    else:
        print(response["message"])
        return None

def check_parking_spots():
    """Retrieve available parking spots."""
    response = send_request("get_parking_spots")
    if response["status"] == "success":
        spots = response["spots"]
        print("\nParking Spots:")
        for spot in spots:
            print(f"ID: {spot['id']} - Status: {spot['status']}")
    else:
        print("Failed to retrieve parking spots.")

def reserve_spot(user_id):
    """Reserve a parking spot."""
    check_parking_spots()
    spot_id = int(input("\nEnter the ID of the spot you want to reserve: "))
    response = send_request("reserve_spot", {"user_id": user_id, "spot_id": spot_id})
    print(response["message"])

def check_parking_history(user_id):
    """Retrieve the user's parking history."""
    response = send_request("get_parking_history", {"user_id": user_id})
    if response["status"] == "success":
        history = response["history"]
        print("\nParking History:")
        for entry in history:
            print(f"Date: {entry['parking_date']}, Time: {entry['parking_time']}")
    else:
        print(response["message"])



def add_parking_spot():
    """Request the server to add a new parking spot."""
    response = send_request("add_parking_spot")
    print(response["message"])

def main():
    """Main menu for client interactions."""
    print("\n🚗 Welcome to ParkScout Client 🚗")
    user_id = None

    while True:
        print("\n1. Register")
        print("2. Login")
        print("3. Check Parking Spots")
        print("4. Reserve a Parking Spot")
        print("5. View Parking History")
        print("6. Exit")
        print("7. Add Parking Spot")
        choice = input("Select an option: ")

        if choice == "1":
            register()
        elif choice == "2":
            user_id = login()
        elif choice == "3":
            check_parking_spots()
        elif choice == "4":
            if user_id:
                reserve_spot(user_id)
            else:
                print("You need to login first.")
        elif choice == "5":
            if user_id:
                check_parking_history(user_id)
            else:
                print("You need to login first.")
        elif choice == "6":
            print("Exiting ParkScout client. Goodbye! 🚗")
            break
        elif choice == "7":
            add_parking_spot()

        else:
            print("Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    main()
