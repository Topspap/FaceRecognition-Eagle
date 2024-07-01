import os
from deepface import DeepFace
import cv2

# User Inputs:
input_folder_path = r".\convertToFaces_input"
output_folder_path = r".\convertedFaces_output"

# Model/Script Properties:
model_name = "Facenet512"
detector_backend = "fastmtcnn"
expand_percentage = 20  # How much to expand the face cropping area in percentage %, Keep Constant through all Database
threshold = 500

def list_files(folder_path):
    """
    Lists all files in a folder and its subfolders recursively.
    Args:
        folder_path (string): Path to the folder.
    Returns:
        All files in a folder and its subfolders recursively.
    """
    all_files = []
    for root, dirs, files in os.walk(folder_path):
        # Print the full path of each file
        for filename in files:
            file_path = os.path.join(root, filename)
            all_files.append(file_path)
            # print(os.path.join(root, filename))
    return all_files


def change_root_path(file_path, old_root, new_root):
    """
    Changes the root path of a file path using os.path.join.

    Args:
      file_path: The original path to the file.
      old_root: The root path to be replaced.
      new_root: The new root path to use.

    Returns:
      The new path with the replaced root.
    """
    # Split the path into parts
    path_parts = file_path.split(os.sep)

    # Find the index of the old root (assuming it's a single directory)
    try:
        root_index = path_parts.index(old_root)
    except ValueError:
        print(f"Old root path '{old_root}' not found in '{file_path}'.")
        return file_path

    # Replace the root part with the new root
    path_parts[root_index] = new_root

    # Join the path parts back together
    new_path = os.path.join(*path_parts)
    return new_path


def clip_coordinates(facial_area, image_width, image_height):
    """
    Clips the coordinates of a facial area dictionary to stay within image borders.

    Args:
        facial_area: A dictionary or pandas containing facial area information.
        image_width: The width of the image.
        image_height: The height of the image.

    Returns:
        A new dictionary with clipped coordinates.
    """

    if "dict" in str(type(facial_area)):
        clipped_area = {}
        clipped_area['x'] = max(0, min(facial_area['x'], image_width - 1))
        clipped_area['y'] = max(0, min(facial_area['y'], image_height - 1))
        clipped_area['w'] = min(facial_area['w'], image_width - clipped_area['x'])
        clipped_area['h'] = min(facial_area['h'], image_height - clipped_area['y'])
        return clipped_area

    elif "pandas" in str(type(facial_area)):
        clipped_area = {}
        clipped_area['x'] = max(0, min(facial_area['source_x'][0], image_width - 1))
        clipped_area['y'] = max(0, min(facial_area['source_y'][0], image_height - 1))
        clipped_area['w'] = min(facial_area['source_w'][0], image_width - clipped_area['x'])
        clipped_area['h'] = min(facial_area['source_h'][0], image_height - clipped_area['y'])
        return clipped_area


def create_unique_image_name(folder_path, original_name):
    """
    Creates a folder with a unique name based on the original name and then add "_" and incrementing number.

    Args:
      folder_path: The folder path where the file will be created.
      original_name: The original name of the image.

    Returns:
      The path with unique name of image.
    """
    num = 0
    while True:
        file_name = f"{original_name}_{num}.jpg"
        file_path = os.path.join(folder_path, file_name)
        if not os.path.exists(file_path):
            return file_path
        num += 1


def crop_face(original_image, facial_area):
    """
    Checks if two images are identical using pixel-by-pixel comparison.

    Args:
      original_image : the original image loaded by cv2.
      facial_area : the dictionary or pandas containing facial area information.

    Returns:
      cropped_face: the cropped face, ready to save.
    """
    clipped_area = clip_coordinates(facial_area, original_image.shape[1], original_image.shape[
        0])  # Get the image cropping area, Assuming image is a NumPy array

    # Use clipped_area for cropping:
    cropped_face = original_image[clipped_area['y']:clipped_area['y'] + clipped_area['h'],
                   clipped_area['x']:clipped_area['x'] + clipped_area['w']]

    return cropped_face

# ----------------------------------------------------------------------------------------------------


# Create script folders (input_folder_path, output_folder_path)
script_folder_list = [input_folder_path, output_folder_path]
for folder in script_folder_list:
    # Check if the folder exists
    if not os.path.exists(folder):
        # Create the folder if it doesn't exist
        os.makedirs(folder)
        print(f"Folder '{folder}' created successfully.")
    else:
        print(f"Folder '{folder}' already exists.")


all_files = list_files(input_folder_path)
# print(all_files)

# Extract faces using DeepFace and save them in output_folder_path:
for file in all_files:
    try:
        # Detect and Extract the face:
        extracted_face = DeepFace.extract_faces(img_path=str(file), enforce_detection=True,
                                                detector_backend=detector_backend, expand_percentage=expand_percentage)

        img = cv2.imread(str(file))  # Read the image
        for face in range(len(extracted_face)):
            facial_area = extracted_face[face]['facial_area']  # Get the facial area from DeepFace.extract_faces result
            cropped_face = crop_face(img, facial_area)  # Crop the Face from original image

            # Save cropped_face to convertedFaces_output in same subfolder name:
            new_root_path = change_root_path(file, input_folder_path.split("\\")[-1], output_folder_path.split("\\")[-1])
            new_root_path_no_ext = new_root_path.rsplit(".", 1)[0]
            new_image_save_path = f"{new_root_path_no_ext}.jpg"
            new_image_name = new_image_save_path.split("\\")[-1]
            new_image_name_no_ext = new_image_name.rsplit(".", 1)[0]

            # Try to create the directory (and any missing parent directories)
            directory = os.path.dirname(new_image_save_path)
            try:
                os.makedirs(directory, exist_ok=True)  # exist_ok avoids errors if directory exists
            except OSError:
                print(f"Error creating directory: {directory}")

            if os.path.exists(new_image_save_path):
                print("File with same name already exists!")
                new_root_path_only = new_root_path_no_ext.rsplit("\\", 1)[0]
                unique_name = create_unique_image_name(directory, new_image_name_no_ext)
                cv2.imwrite(unique_name, cropped_face)
                print("Face cropped and saved successfully! with unique name")

            else:
                cv2.imwrite(new_image_save_path, cropped_face)
                print(f"Face cropped and saved successfully!, to Folder: {new_image_save_path}")

    except Exception as e:
        if "Face could not be detected" in str(e):  # Handel Face could not be detected
            print(f"Face could not be detected in {file}")
        else:
            print(e)  # Handel Other Errors

print("Process Done!")
