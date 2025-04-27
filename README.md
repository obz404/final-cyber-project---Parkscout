# 🚗 ParkScout — Intelligent Parking Spot Detection System

ParkScout is a smart parking system that detects whether parking spots are **occupied**, **reserved**, or **available** using **live camera feed**, **TensorFlow deep learning**, and a **Flask web dashboard**.

🔵 Live camera streams monitor parking spots  
🔵 Real-time automatic updates without refreshing  
🔵 Web dashboard for users and admins  
🔵 Admins can add or remove parking spots  
🔵 Machine learning model retrained easily with real-world data

---

## 📋 Features

- **Multiple Cameras and Multiple Spots** supported
- **Real-Time Status Updates** (auto-refresh every few seconds)
- **AES-encrypted Communication** between camera, server, and web app
- **Flask Web App**:
  - View parking availability (live)
  - Reserve available spots
  - View parking history
- **Admin Panel**:
  - Add new parking spots
  - Remove parking spots
  - Monitor and manage all spot statuses
- **Live Camera Streaming** per spot
- **Model Retraining** using real-world photos

---

## 🛠 Project Structure

| Folder / File | Description |
|:--------------|:------------|
| `server.py` | Handles user login, registration, spot status management, AES encryption |
| `camera_predict.py` | Reads live camera feed, predicts spot status, updates server automatically |
| `app.py` | Flask web app: user login, reserve, dashboard, camera feed |
| `ml_model/` | Contains the ML model + training scripts (`train_model.py`, `evaluate_model.py`) |
| `cropped_dataset/` | Training images (organized into `empty_spots/` and `occupied_spots/`) |
| `static/` | Stylesheets, saved live camera images, placeholder image |
| `templates/` | HTML templates (`home.html`, `admin_dashboard.html`, etc.) |
| `live_camera_sample_collector.py` | Script to capture and save training images manually |

---

## 🚀 How to Run

1. **Clone the Repository**  
```bash
git clone https://github.com/obz404/final-cyber-project---Parkscout.git
cd final-cyber-project---Parkscout
Install Requirements

bash
Copy
Edit
pip install -r requirements.txt
(or manually install: flask, tensorflow, opencv-python, scikit-learn, matplotlib, sqlalchemy, Werkzeug)

Run the Server

bash
Copy
Edit
python server.py
Start the Camera Predictor for Each Spot
(Example: Spot 1 uses Camera 0)

bash
Copy
Edit
python camera_predict.py 1 0
(Use --headless if you don't want to display camera window.)

Run the Flask Web App

bash
Copy
Edit
python app.py
Access the Web App
Open browser and go to:

cpp
Copy
Edit
http://127.0.0.1:5000
🧠 Training a New Model
If you collect new images:

Save images into:

cropped_dataset/empty_spots/

cropped_dataset/occupied_spots/

Retrain the model:

bash
Copy
Edit
python ml_model/train_model.py
✅ Model will be saved automatically as ml_model/parking_model.h5.

You can also evaluate it using:

bash
Copy
Edit
python ml_model/evaluate_model.py
🎥 Live Camera Feed
Each parking spot has its own live video feed.
The feed shows a cropped rectangle and a label (EMPTY / OCCUPIED) in real-time.

If the camera is disconnected, a placeholder image is shown instead.

🎯 Technologies Used
Python 3.11

Flask (Web Framework)

TensorFlow / Keras (Deep Learning)

OpenCV (Camera Streaming)

SQLAlchemy (Database ORM)

AES Encryption (Secure communication)

Bootstrap/Custom CSS (Frontend)

📸 Screenshot
![image](https://github.com/user-attachments/assets/a9d8e3f8-588d-4259-8d11-89d96132fd82)
![image](https://github.com/user-attachments/assets/71488ab2-de3c-49b3-8314-09d8b05a10f5)
![image](https://github.com/user-attachments/assets/5f5c1e37-2e50-4ae5-814d-0312eb4b3e20)


markdown
Copy
Edit
![ParkScout Dashboard](static/project_screenshot.png)
📢 Notes
Parking spot statuses update automatically every few seconds (AJAX polling).

Model retraining is simple and fully integrated.

Admins can manage parking spots via a separate dashboard.

Each camera can monitor a different spot independently.

Database (parking.db) stores users, parking spots, and parking history.

🤝 Acknowledgments
This project was developed for the Cyber Final Project.

Special thanks to all testers and helpers during the development phase!
