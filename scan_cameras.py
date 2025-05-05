"""
scan_cameras.py

A simple script to detect connected webcams using OpenCV.

This script attempts to open camera indices from 0 up to a specified maximum.
For each index, it prints whether a camera is found and returns a list of successful indices.
"""

import cv2

def scan_cameras(max_index=5):
    """
    Scan for connected cameras by attempting to open each index.

    Args:
        max_index (int): Number of camera indices to scan (will try from 0 to max_index-1).

    Returns:
        List[int]: Indices where cameras were successfully opened and a frame was read.
    """
    found_indices = []
    print("🔍 Scanning for connected cameras...")

    for index in range(max_index):
        # Attempt to initialize video capture on the current index
        cap = cv2.VideoCapture(index)

        # Check if the camera device was opened successfully
        if not cap.isOpened():
            print(f"❌ No camera at index {index}")
        else:
            # Try to read a single frame to verify the stream
            ret, _ = cap.read()
            if ret:
                print(f"✅ Camera found at index {index}")
                found_indices.append(index)
            else:
                print(f"❌ Camera at index {index} opened but failed to read frame")

        # Always release the capture device to free the resource
        cap.release()

    return found_indices

if __name__ == "__main__":
    """
    Entry point: scan for up to 5 cameras (indices 0–4) and display results.
    """
    scan_cameras()
