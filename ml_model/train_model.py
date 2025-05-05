"""
train_model.py

Retrains a convolutional neural network to classify parking spot images
as 'empty' or 'occupied', using data augmentation and early stopping.
Loads images from a directory structured by class labels, applies preprocessing,
builds and trains a TensorFlow Keras model, and saves the trained model to disk.

Usage:
    python train_model.py

Outputs:
    - ml_model/parking_model.h5 : Saved Keras model for inference in camera_predict.py
"""

import os
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping

# -------------------------------------------------------------------
# Configuration: paths and hyperparameters
# -------------------------------------------------------------------
DATASET_PATH = 'cropped_dataset'   # Root folder with subfolders for 'empty' and 'occupied'
IMG_WIDTH    = 360                 # Width of input images (pixels)
IMG_HEIGHT   = 102                 # Height of input images (pixels)
BATCH_SIZE   = 32                  # Number of images per gradient update
EPOCHS       = 20                  # Maximum number of training epochs

# -------------------------------------------------------------------
# Data Augmentation and Preprocessing
# -------------------------------------------------------------------
# Apply random transformations to increase training robustness
train_datagen = ImageDataGenerator(
    rescale=1.0 / 255,            # Normalize pixel values to [0,1]
    validation_split=0.2,         # Reserve 20% of data for validation
    rotation_range=20,            # Random rotations up to 20°
    width_shift_range=0.2,        # Horizontal shifts up to 20%
    height_shift_range=0.2,       # Vertical shifts up to 20%
    zoom_range=0.3,               # Zoom in/out up to 30%
    brightness_range=[0.5, 1.5],  # Random brightness adjustments
    shear_range=0.2,              # Random shear transformations
    horizontal_flip=True,         # Random horizontal flips
    fill_mode='nearest'           # Fill empty pixels after transform
)

# Only rescaling for validation set
val_datagen = ImageDataGenerator(
    rescale=1.0 / 255,
    validation_split=0.2
)

# Load training dataset from directory with subfolders for each class
train_ds = train_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=(IMG_HEIGHT, IMG_WIDTH),  # Resize images to model input size
    batch_size=BATCH_SIZE,
    class_mode='binary',                  # Two classes: empty vs. occupied
    subset='training',
    seed=123                              # Seed for reproducibility
)

# Load validation dataset
val_ds = val_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=(IMG_HEIGHT, IMG_WIDTH),
    batch_size=BATCH_SIZE,
    class_mode='binary',
    subset='validation',
    seed=123
)

# -------------------------------------------------------------------
# Model Architecture
# -------------------------------------------------------------------
model = keras.Sequential([
    # Input layer expecting images of shape (IMG_HEIGHT, IMG_WIDTH, 3)
    layers.Input(shape=(IMG_HEIGHT, IMG_WIDTH, 3)),

    # Convolutional block 1
    layers.Conv2D(32, (3, 3), activation='relu'),
    layers.MaxPooling2D(),

    # Convolutional block 2
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D(),

    # Convolutional block 3
    layers.Conv2D(128, (3, 3), activation='relu'),
    layers.MaxPooling2D(),

    # Flatten feature maps to a 1D vector
    layers.Flatten(),

    # Dropout for regularization
    layers.Dropout(0.4),

    # Fully connected layer
    layers.Dense(128, activation='relu'),

    # Output layer with sigmoid for binary classification
    layers.Dense(1, activation='sigmoid')
])

# -------------------------------------------------------------------
# Compile Model
# -------------------------------------------------------------------
model.compile(
    optimizer='adam',               # Adaptive learning rate optimization
    loss='binary_crossentropy',     # Suitable for binary classification
    metrics=['accuracy']            # Track accuracy during training
)

# -------------------------------------------------------------------
# Callbacks
# -------------------------------------------------------------------
# Stop training early if validation loss does not improve for 3 epochs
early_stop = EarlyStopping(
    monitor='val_loss',
    patience=3,
    restore_best_weights=True
)

# -------------------------------------------------------------------
# Train Model
# -------------------------------------------------------------------
history = model.fit(
    train_ds,                       # Training data generator
    validation_data=val_ds,         # Validation data generator
    epochs=EPOCHS,
    callbacks=[early_stop]          # Early stopping callback
)

# -------------------------------------------------------------------
# Save Trained Model
# -------------------------------------------------------------------
os.makedirs('ml_model', exist_ok=True)             # Ensure output folder exists
model.save('ml_model/parking_model.h5')            # Persist model for inference
print("✅ Model retrained and saved to 'ml_model/parking_model.h5'")
