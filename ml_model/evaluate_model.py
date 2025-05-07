"""
evaluate_model.py

Evaluates the performance of the trained parking spot classifier on the validation set.
Loads the saved Keras model, prepares the validation data generator,
computes predictions, and prints a classification report.
Also plots a confusion matrix to visualize true vs. predicted labels.

Usage:
    python evaluate_model.py
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    ConfusionMatrixDisplay
)
import matplotlib.pyplot as plt

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
# Path to the saved model
MODEL_PATH = 'ml_model/parking_model.h5'

# Validation dataset directory (same structure as used for training)
DATASET_PATH = 'cropped_dataset'

# Image dimensions must match those used during training
IMG_WIDTH  = 360
IMG_HEIGHT = 102

# Batch size for evaluation
BATCH_SIZE = 32

# -------------------------------------------------------------------
# Load the trained model
# -------------------------------------------------------------------
model = tf.keras.models.load_model(MODEL_PATH)
print(f"✅ Loaded model from '{MODEL_PATH}'")

# -------------------------------------------------------------------
# Prepare the validation data generator
# -------------------------------------------------------------------
val_datagen = ImageDataGenerator(
    rescale=1.0 / 255,       # Normalize pixel values to [0,1]
    validation_split=0.2      # Reserve 20% of data for validation
)

# Create validation dataset iterator
val_ds = val_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=(IMG_HEIGHT, IMG_WIDTH),  # Resize images to model input
    batch_size=BATCH_SIZE,
    class_mode='binary',                  # Binary labels: empty vs. occupied
    subset='validation',                  # Use the validation split
    shuffle=False                         # Keep order for label alignment
)

# -------------------------------------------------------------------
# Generate predictions on the validation set
# -------------------------------------------------------------------
# model.predict returns an array of probabilities
y_pred_probs = model.predict(val_ds, verbose=0)

# Convert probabilities to binary class predictions (threshold 0.5)
y_pred_classes = (y_pred_probs > 0.5).astype(int).reshape(-1)

# True labels from the generator
y_true = val_ds.classes

# Get human-readable class names from the generator
class_names = list(val_ds.class_indices.keys())

# -------------------------------------------------------------------
# Print classification report
# -------------------------------------------------------------------
print("\nClassification Report:")
print(classification_report(
    y_true,
    y_pred_classes,
    target_names=class_names
))

# -------------------------------------------------------------------
# Plot confusion matrix
# -------------------------------------------------------------------
cm = confusion_matrix(y_true, y_pred_classes)
disp = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=class_names
)

# Create the plot (uses matplotlib)
disp.plot(cmap=plt.cm.Blues)
plt.title('Confusion Matrix')
plt.tight_layout()

# Show the plot window
plt.show()


