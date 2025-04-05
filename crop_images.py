import os
import cv2

# Folders
DATASET_FOLDER = 'dataset'  # Your original full images
CROPPED_FOLDER = 'cropped_dataset'  # Where cropped images will go

# Updated cropping area (x, y, width, height)
CROP_X = 140
CROP_Y = 250
CROP_W = 360
CROP_H = 180

# Loop over the two classes
for label in ['empty', 'occupied']:
    input_path = os.path.join(DATASET_FOLDER, label)
    output_subfolder = f"cropped_{label}"  # Like 'cropped_empty' and 'cropped_occupied'
    output_path = os.path.join(CROPPED_FOLDER, output_subfolder)

    # Create the output folder if it doesn't exist
    os.makedirs(output_path, exist_ok=True)

    # Loop over all images inside the input folder
    for filename in os.listdir(input_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_path = os.path.join(input_path, filename)
            image = cv2.imread(img_path)

            if image is None:
                print(f"⚠️ Warning: Couldn't read image {img_path}")
                continue

            # Crop the image
            cropped_image = image[CROP_Y:CROP_Y+CROP_H, CROP_X:CROP_X+CROP_W]

            # Save it in the correct cropped subfolder
            output_img_path = os.path.join(output_path, filename)
            cv2.imwrite(output_img_path, cropped_image)

print("✅ Done! Cropped images saved to 'cropped_dataset/cropped_empty/' and 'cropped_dataset/cropped_occupied/'.")
