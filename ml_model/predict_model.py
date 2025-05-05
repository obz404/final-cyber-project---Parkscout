"""
predict_model.py

Command-line utility to classify a single parking spot image as EMPTY or OCCUPIED
using a pre-trained TensorFlow Keras model.

Usage:
    python predict_model.py <path_to_image>

Outputs:
    Prints "🅿️  Spot is EMPTY" if the model predicts empty,
    or "🚗  Spot is OCCUPIED" if the model predicts occupied.
"""

import os
import sys

import cv2
import numpy as np
import tensorflow as tf

# -------------------------------------------------------------------
# Configuration: model path and crop settings (must match training)
# -------------------------------------------------------------------
MODEL_PATH = 'ml_model/parking_model.h5'

# Region of interest (ROI) for cropping from full image: (x, y, width, height)
CROP_X = 140
CROP_Y = 250
CROP_W = 360
CROP_H = 180

# -------------------------------------------------------------------
# Load the trained model once at module import
# -------------------------------------------------------------------
try:
    model = tf.keras.models.load_model(MODEL_PATH)
except Exception as e:
    print(f"❌ Failed to load model from '{MODEL_PATH}': {e}")
    sys.exit(1)

def prepare_image(image_path: str) -> np.ndarray:
    """
    Load an image from disk, crop to the ROI, resize, normalize, and add batch dimension.

    Args:
        image_path (str): Path to the input image file.

    Returns:
        np.ndarray: Preprocessed image tensor of shape (1, IMG_H, IMG_W, 3).

    Raises:
        ValueError: If the image cannot be loaded.
    """
    # Read the image from file
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"❌ Error loading image: {image_path}")

    # Crop to the same region used during training
    cropped_img = img[CROP_Y:CROP_Y + CROP_H, CROP_X:CROP_X + CROP_W]

    # Resize to the model's expected input dimensions (width, height)
    cropped_img = cv2.resize(cropped_img, (CROP_W, CROP_H))

    # Normalize pixel values to [0, 1]
    cropped_img = cropped_img.astype(np.float32) / 255.0

    # Add a batch dimension so shape is (1, height, width, channels)
    return np.expand_dims(cropped_img, axis=0)

def predict(image_path: str) -> None:
    """
    Perform a single inference on the provided image and print the result.

    Args:
        image_path (str): Path to the image file to classify.
    """
    try:
        img_tensor = prepare_image(image_path)
    except ValueError as ve:
        print(ve)
        return

    # Run the model prediction (sigmoid output)
    score = model.predict(img_tensor, verbose=0)[0][0]

    # Interpret probability threshold 0.5
    if score < 0.5:
        print("🅿️  Spot is EMPTY")
    else:
        print("🚗  Spot is OCCUPIED")

def main():
    """
    Parse command-line arguments and invoke prediction.
    Exits with usage instructions if input is invalid.
    """
    if len(sys.argv) != 2:
        print("Usage: python predict_model.py <path_to_image>")
        sys.exit(1)

    image_path = sys.argv[1]
    if not os.path.isfile(image_path):
        print(f"❌ Error: '{image_path}' does not exist or is not a file.")
        sys.exit(1)

    predict(image_path)

if __name__ == "__main__":
    main()
