import tensorflow as tf
import numpy as np
import cv2
import sys
import os

# Load the trained model
model = tf.keras.models.load_model('ml_model/parking_model.h5')

# Crop settings (same as used during training)
CROP_X = 140
CROP_Y = 300
CROP_W = 360
CROP_H = 120

# Function to load, crop, and prepare the image
def prepare_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"❌ Error loading image: {image_path}")

    # Crop the image
    cropped_img = img[CROP_Y:CROP_Y+CROP_H, CROP_X:CROP_X+CROP_W]

    # Resize to training size
    cropped_img = cv2.resize(cropped_img, (360, 102))  # (width, height)

    # Normalize
    cropped_img = cropped_img / 255.0

    # Add batch dimension
    cropped_img = np.expand_dims(cropped_img, axis=0)

    return cropped_img

# Function to predict
def predict(image_path):
    img = prepare_image(image_path)
    prediction = model.predict(img)[0][0]  # Get prediction probability

    if prediction < 0.5:
        print("🅿️  Spot is EMPTY")
    else:
        print("🚗  Spot is OCCUPIED")

# Command-line usage
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ml_model/predict_model.py <path_to_image>")
    else:
        image_path = sys.argv[1]
        if not os.path.exists(image_path):
            print(f"Error: {image_path} does not exist.")
        else:
            predict(image_path)
