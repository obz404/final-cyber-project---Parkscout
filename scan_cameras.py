import cv2

print("🔍 Scanning for connected cameras...")

for index in range(5):  # Try camera indexes 0 to 4
    cap = cv2.VideoCapture(index)
    if cap.read()[0]:
        print(f"✅ Camera found at index {index}")
        cap.release()
    else:
        print(f"❌ No camera at index {index}")
