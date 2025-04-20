import tensorflow as tf
import numpy as np
import cv2

# Load the trained model
model = tf.keras.models.load_model('ml_model/parking_model.h5')

# Crop settings (same as during training)
CROP_X = 140
CROP_Y = 250
CROP_W = 360
CROP_H = 180

# Start webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame")
        break

    # Crop the parking area
    cropped = frame[CROP_Y:CROP_Y+CROP_H, CROP_X:CROP_X+CROP_W]
    resized = cv2.resize(cropped, (360, 102)) / 255.0
    input_img = np.expand_dims(resized, axis=0)

    # Predict
    prediction = model.predict(input_img)[0][0]
    label = "🅿️ EMPTY" if prediction < 0.5 else "🚗 OCCUPIED"
    color = (0, 255, 0) if prediction < 0.5 else (0, 0, 255)

    # Draw prediction on original frame
    if prediction < 0.5:
        label = "EMPTY"
    else:
        label = "OCCUPIED"

    cv2.putText(frame, label, (CROP_X, CROP_Y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)

    cv2.rectangle(frame, (CROP_X, CROP_Y), (CROP_X+CROP_W, CROP_Y+CROP_H), color, 2)

    # Show the frame
    cv2.imshow("Parking Spot Detector", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
