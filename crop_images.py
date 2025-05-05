"""
crop_images.py

A utility script to crop images from a labeled dataset into a fixed region of interest (ROI).
Crops and saves 'empty' and 'occupied' class images into separate subfolders under the output folder.
"""

import os
import cv2

def crop_images(dataset_folder='dataset',
                output_folder='cropped_dataset',
                crop_x=140, crop_y=250, crop_w=360, crop_h=180,
                classes=('empty', 'occupied')):
    """
    Crop images in a dataset and save them to a new folder structure.

    Args:
        dataset_folder (str): Path to the root folder containing class subfolders with full-size images.
        output_folder (str): Path to the root folder where cropped images will be saved.
        crop_x (int): X-coordinate of the top-left corner of the crop rectangle.
        crop_y (int): Y-coordinate of the top-left corner of the crop rectangle.
        crop_w (int): Width of the cropping rectangle.
        crop_h (int): Height of the cropping rectangle.
        classes (tuple of str): Names of the class subfolders to process (e.g., 'empty', 'occupied').

    Returns:
        None
    """
    # Ensure the output root folder exists
    os.makedirs(output_folder, exist_ok=True)

    for label in classes:
        # Build input and output paths for the current class
        input_path = os.path.join(dataset_folder, label)
        output_subfolder = f"cropped_{label}"
        output_path = os.path.join(output_folder, output_subfolder)

        # Create the output subfolder for this class
        os.makedirs(output_path, exist_ok=True)

        # Iterate over image files in the input folder
        for filename in os.listdir(input_path):
            # Process only common image file extensions
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue

            img_path = os.path.join(input_path, filename)
            # Read the image from disk
            image = cv2.imread(img_path)
            if image is None:
                # Warn if the image could not be read (e.g., corrupted file)
                print(f"⚠️ Warning: Couldn't read image {img_path}")
                continue

            # Perform the crop using array slicing: image[y:y+h, x:x+w]
            cropped_image = image[crop_y:crop_y + crop_h,
                                  crop_x:crop_x + crop_w]

            # Save the cropped image to the corresponding output folder
            output_img_path = os.path.join(output_path, filename)
            success = cv2.imwrite(output_img_path, cropped_image)
            if not success:
                print(f"❌ Failed to write cropped image to {output_img_path}")

    print(f"✅ Done! Cropped images saved under '{output_folder}'.")

if __name__ == "__main__":
    # Entry point: crop images using default parameters
    crop_images()
