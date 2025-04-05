# ml_model/train_model.py

import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models
import os

# Paths to your folders
dataset_dir = os.path.join(os.getcwd(), 'dataset')
 # Go back to project root
train_data_dir = dataset_dir  # Empty and occupied folders are here

# Create image generators
datagen = ImageDataGenerator(
    rescale=1.0/255,
    validation_split=0.2  # 20% for validation
)

train_generator = datagen.flow_from_directory(
    train_data_dir,
    target_size=(150, 150),
    batch_size=16,
    class_mode='binary',
    subset='training'
)

val_generator = datagen.flow_from_directory(
    train_data_dir,
    target_size=(150, 150),
    batch_size=16,
    class_mode='binary',
    subset='validation'
)

# Build a simple CNN model
model = models.Sequential([
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(150, 150, 3)),
    layers.MaxPooling2D(2, 2),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D(2, 2),
    layers.Conv2D(128, (3, 3), activation='relu'),
    layers.MaxPooling2D(2, 2),
    layers.Flatten(),
    layers.Dense(128, activation='relu'),
    layers.Dense(1, activation='sigmoid')  # Binary classification: empty or occupied
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

# Train the model
history = model.fit(
    train_generator,
    validation_data=val_generator,
    epochs=10
)

# Save the model
model.save('ml_model/parking_model.h5')
print("✅ Model saved to ml_model/parking_model.h5")
