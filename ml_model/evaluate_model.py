import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import confusion_matrix, classification_report, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

# Load model
model = tf.keras.models.load_model('ml_model/parking_model.h5')

# Prepare validation dataset (the same cropped_dataset you used)
DATASET_PATH = 'cropped_dataset'
IMG_WIDTH = 360
IMG_HEIGHT = 102
BATCH_SIZE = 32

val_datagen = ImageDataGenerator(rescale=1./255, validation_split=0.2)

val_ds = val_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=(IMG_HEIGHT, IMG_WIDTH),
    batch_size=BATCH_SIZE,
    class_mode='binary',
    subset='validation',
    shuffle=False  # Important for matching labels to predictions
)

# Predict
y_pred = model.predict(val_ds)
y_pred_classes = (y_pred > 0.5).astype(int).reshape(-1)
y_true = val_ds.classes

# Evaluation metrics
print("\nClassification Report:")
print(classification_report(y_true, y_pred_classes, target_names=list(val_ds.class_indices.keys())))

# Confusion Matrix
cm = confusion_matrix(y_true, y_pred_classes)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=list(val_ds.class_indices.keys()))
disp.plot(cmap=plt.cm.Blues)
plt.title('Confusion Matrix')
plt.show()
