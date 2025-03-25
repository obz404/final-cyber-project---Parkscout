import cv2
import os
import time

# Create directories if they don't exist (for manual sorting later)
os.makedirs("empty_spots", exist_ok=True)
os.makedirs("occupied_spots", exist_ok=True)


def capture_image(save_folder="empty_spots"):
    timestamp = int(time.time())  # Unique timestamp for filenames
    filename = os.path.join(save_folder, f"spot_{timestamp}.jpg")

    # Save image to the selected folder
    cv2.imwrite(filename, frame)
    print(f"✅ Image saved: {filename} (Move it manually to the correct folder)")


# Open the camera
cam = cv2.VideoCapture(0)  # Use USB Camera (0 = default camera)

if not cam.isOpened():
    print("❌ Error: Camera not detected.")
else:
    print("✅ Camera detected! Press 'C' to capture an image, 'Q' to quit.")

while True:
    ret, frame = cam.read()  # Capture a frame

    if not ret:
        print("❌ Failed to capture frame.")
        break

    # Show the live feed in a window
    cv2.imshow("Live Parking Spot Feed", frame)

    # Wait for keypress
    key = cv2.waitKey(1) & 0xFF

    if key == ord("c"):  # Press 'C' to capture an image
        capture_image()

    elif key == ord("q"):  # Press 'Q' to quit
        print("🚪 Exiting...")
        break

# Release camera and close windows
cam.release()
cv2.destroyAllWindows()
