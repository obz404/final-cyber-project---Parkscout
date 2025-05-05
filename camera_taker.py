"""
camera_taker.py

A utility script to capture live parking spot images from a webcam,
label them as 'empty' or 'occupied', and save both the full-frame
and cropped ROI images into organized folders.

Usage:
    1. Run the script: python camera_taker.py
    2. A live video window will open with a yellow rectangle indicating
       the crop area.
    3. Press 'E' to label the current frame as EMPTY.
    4. Press 'O' to label the current frame as OCCUPIED.
    5. Press 'Q' to quit the application.
"""

import cv2
import os
import time

# -------------------------------------------------------------------
# Configuration: folder names and crop rectangle
# -------------------------------------------------------------------

# Folders for full-frame captures
FULL_EMPTY_FOLDER    = "empty_spots"
FULL_OCCUPIED_FOLDER = "occupied_spots"

# Folders for cropped ROI images
CROPPED_EMPTY_FOLDER    = "cropped_dataset/cropped_empty"
CROPPED_OCCUPIED_FOLDER = "cropped_dataset/cropped_occupied"

# Region of interest (ROI) to crop: (x, y, width, height)
CROP_X = 140
CROP_Y = 250
CROP_W = 360
CROP_H = 180

# Camera index to open (0 is usually the default webcam)
CAMERA_INDEX = 0

def ensure_folders_exist():
    """
    Create the necessary folders for saving images if they don't already exist.
    """
    for folder in [
        FULL_EMPTY_FOLDER,
        FULL_OCCUPIED_FOLDER,
        CROPPED_EMPTY_FOLDER,
        CROPPED_OCCUPIED_FOLDER
    ]:
        os.makedirs(folder, exist_ok=True)

def capture_and_label_spots():
    """
    Open the webcam feed, display a live rectangle for the crop area,
    and respond to keypresses to save labeled images.
    """
    # Initialize webcam capture
    cam = cv2.VideoCapture(CAMERA_INDEX)
    if not cam.isOpened():
        print("❌ Error: Camera not detected.")
        return

    print("✅ Camera detected! Press 'E' for empty, 'O' for occupied, 'Q' to quit.")

    try:
        while True:
            # Read a frame from the webcam
            ret, frame = cam.read()
            if not ret:
                print("❌ Failed to capture frame.")
                break

            # Draw the cropping rectangle in yellow (BGR: 0,255,255)
            cv2.rectangle(
                frame,
                (CROP_X, CROP_Y),
                (CROP_X + CROP_W, CROP_Y + CROP_H),
                (0, 255, 255),
                2
            )

            # Display the live feed window
            cv2.imshow("Live Parking Spot Feed", frame)

            # Wait for a key press for 1ms
            key = cv2.waitKey(1) & 0xFF

            # Use timestamp as unique filename
            timestamp = int(time.time())

            if key == ord("e"):
                # Label as EMPTY: save full-frame and crop
                filename = f"spot_{timestamp}.jpg"
                full_path    = os.path.join(FULL_EMPTY_FOLDER, filename)
                cropped_path = os.path.join(CROPPED_EMPTY_FOLDER, filename)

                cv2.imwrite(full_path, frame)
                cropped = frame[CROP_Y:CROP_Y + CROP_H, CROP_X:CROP_X + CROP_W]
                cv2.imwrite(cropped_path, cropped)

                print(f"✅ Saved EMPTY image: {full_path} and cropped to {cropped_path}")

            elif key == ord("o"):
                # Label as OCCUPIED: save full-frame and crop
                filename = f"spot_{timestamp}.jpg"
                full_path    = os.path.join(FULL_OCCUPIED_FOLDER, filename)
                cropped_path = os.path.join(CROPPED_OCCUPIED_FOLDER, filename)

                cv2.imwrite(full_path, frame)
                cropped = frame[CROP_Y:CROP_Y + CROP_H, CROP_X:CROP_X + CROP_W]
                cv2.imwrite(cropped_path, cropped)

                print(f"✅ Saved OCCUPIED image: {full_path} and cropped to {cropped_path}")

            elif key == ord("q"):
                # Quit the loop and close the application
                print("🚪 Exiting...")
                break

    finally:
        # Release resources and close windows
        cam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    """
    Entry point: ensure folders exist, then start capture loop.
    """
    ensure_folders_exist()
    capture_and_label_spots()
