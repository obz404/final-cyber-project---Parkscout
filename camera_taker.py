import cv2
import os
import time

# Create full image folders
os.makedirs("empty_spots", exist_ok=True)
os.makedirs("occupied_spots", exist_ok=True)

# Create cropped image folders
os.makedirs("cropped_dataset/cropped_empty", exist_ok=True)
os.makedirs("cropped_dataset/cropped_occupied", exist_ok=True)

# Crop coordinates
CROP_X = 140
CROP_Y = 250
CROP_W = 360
CROP_H = 180

# Open camera
cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("❌ Error: Camera not detected.")
else:
    print("✅ Camera detected! Press 'E' for empty, 'O' for occupied, 'Q' to quit.")

while True:
    ret, frame = cam.read()
    if not ret:
        print("❌ Failed to capture frame.")
        break

    # Draw crop rectangle on live feed
    cv2.rectangle(frame, (CROP_X, CROP_Y), (CROP_X + CROP_W, CROP_Y + CROP_H), (0, 255, 255), 2)
    cv2.imshow("Live Parking Spot Feed", frame)

    key = cv2.waitKey(1) & 0xFF
    timestamp = int(time.time())

    if key == ord("e"):
        filename = f"spot_{timestamp}.jpg"
        full_path = os.path.join("empty_spots", filename)
        cropped_path = os.path.join("cropped_dataset/cropped_empty", filename)

        cv2.imwrite(full_path, frame)
        cropped = frame[CROP_Y:CROP_Y + CROP_H, CROP_X:CROP_X + CROP_W]
        cv2.imwrite(cropped_path, cropped)

        print(f"✅ Saved EMPTY image: {full_path} and cropped to {cropped_path}")

    elif key == ord("o"):
        filename = f"spot_{timestamp}.jpg"
        full_path = os.path.join("occupied_spots", filename)
        cropped_path = os.path.join("cropped_dataset/cropped_occupied", filename)

        cv2.imwrite(full_path, frame)
        cropped = frame[CROP_Y:CROP_Y + CROP_H, CROP_X:CROP_X + CROP_W]
        cv2.imwrite(cropped_path, cropped)

        print(f"✅ Saved OCCUPIED image: {full_path} and cropped to {cropped_path}")

    elif key == ord("q"):
        print("🚪 Exiting...")
        break

cam.release()
cv2.destroyAllWindows()
