# 🚗 ParkScout — Intelligent Parking Spot Detection System

ParkScout is a smart parking system that detects whether parking spots are **occupied** or **available** using **live camera feed**, **TensorFlow deep learning**, and a **Flask web dashboard**.

🔵 Live camera streams monitor parking spots  
🔵 Real-time status prediction (Occupied/Available)  
🔵 Web dashboard for users and admins  
🔵 Admins can manually add or remove parking spots  
🔵 Machine learning model retrained on live real-world data for maximum accuracy

---

## 📋 Features

- **Multiple Cameras Support** (multi-spot)
- **AES-encrypted communication** between camera, server, and web app
- **Flask Web App** for users to:
  - View live parking availability
  - Reserve parking spots
  - See parking history
- **Admin Panel** to:
  - Add/remove parking spots
  - Monitor spot status
- **Live Camera Streaming** inside the dashboard
- **Model retraining** from real-world images

---

## 🛠 Project Structure

| Folder / File | Description |
|:--------------|:------------|
| `server.py` | Handles user login, registration, parking spot status, AES encryption |
| `camera_predict.py` | Reads live camera feed, predicts spot status, updates server |
| `client.py` | (Old) CLI-based user client — replaced by Flask app |
| `app.py` | Flask web app (user login, reserve, admin dashboard, camera feed) |
| `ml_model/` | Contains the machine learning model and training scripts |
| `cropped_dataset/` | Training dataset (empty_spots/occupied_spots folders) |
| `static/` | CSS files, saved camera frames |
| `templates/` | HTML files for the Flask app |
| `live_camera_sample_collector.py` | Script to manually save real-world training images |

---

## 🚀 How to Run

1. **Clone the Repository**  
```bash
git clone https://github.com/obz404/final-cyber-project---Parkscout.git
cd final-cyber-project---Parkscout
Install Requirements
Make sure you are in a virtual environment (venv)

bash
Copy
Edit
pip install -r requirements.txt
(If requirements.txt doesn't exist yet, install manually: flask, tensorflow, scikit-learn, opencv-python, matplotlib)

Run the Server

bash
Copy
Edit
python server.py
Start the Camera Predictor for Each Spot
(Example for Spot 1, Camera 0)

bash
Copy
Edit
python camera_predict.py 1 0
(Add --headless if running without display.)

Run the Flask Web App

bash
Copy
Edit
python app.py
Access the Web App
Go to:

cpp
Copy
Edit
http://127.0.0.1:5000
✅ You can now register, login, reserve spots, view camera, or enter the Admin Dashboard!

🧠 Training a New Model
If you add new images (cropped real images):

Save images into:

cropped_dataset/empty_spots/

cropped_dataset/occupied_spots/

Retrain the model:

bash
Copy
Edit
python ml_model/train_model.py
✅ A new ml_model/parking_model.h5 will be created automatically!

🎯 Technologies Used
Python 3.11

Flask (Web App)

TensorFlow / Keras (Deep Learning Model)

OpenCV (Live Camera Streaming)

SQLAlchemy (Database)

AES Encryption (Secure Communication)

📸 Screenshots
(Add screenshots later if you want:

Dashboard view

Camera feed

Admin panel)

📢 Notes
Cameras and parking spots are fully modular.

The model can be retrained easily when adding real-world data.

Admin access can manually override parking spot status.

🤝 Acknowledgments
This project was developed as part of the Cyber Final Project.

Special thanks to everyone who supported during the testing and training phases!

