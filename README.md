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
