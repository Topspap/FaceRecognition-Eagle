# Tag matched face and create new faces in Database but don't tag them in Eagle as "New Face_{Num}".
import requests
from urllib.parse import unquote
from deepface import DeepFace
import cv2
import os
from PIL import ImageChops
from PIL import Image

# -----------------------------------------------------------
# Eagle default API URL:
BASE_API_URL = "http://localhost:41595"

# Folder to Process:
folderNameToProcess = "FaceReco_Process"

# -----------------------------------------------------------
# User Parameters to change:
database_path = r".\my_db"  # do not give full path it will not get the person name correctly. Give relative path is better.
new_faces_path = fr"{database_path}\[new_faces]"
tempo_folder = r".\tempo"

model_name = "Facenet512"
detector_backend = "fastmtcnn"
distance_metric = "cosine"  # default is "cosine"
expand_percentage = 20  # How much to expand the face cropping area in percentage %
threshold = 500

# -----------------------------------------------------------
# Create script folders (my_db, tempo)
script_folder_list = [database_path, new_faces_path, tempo_folder]
for folder in script_folder_list:
    # Check if the folder exists
    if not os.path.exists(folder):
        # Create the folder if it doesn't exist
        os.makedirs(folder)
        print(f"Folder '{folder}' created successfully.")
    else:
        print(f"Folder '{folder}' already exists.")


def get_folderID(folderName):
    response = requests.get(f'{BASE_API_URL}/api/folder/list')
    data = response.json()

    folders = data['data']

    # Get the folder ID:
    for folder in folders:
        if folder['name'] == folderName:
            folderID = folder['id']
            print("Folder ID is:", folderID, "\n")  # Print folder ID.
    return folderID


def get_items_with_no_FaceTag(max_iterations=None, folderID=None):
    offset = 0
    limit = 200
    items_with_no_FaceTag = []

    while True:
        print(f'Fetching items with offset {offset}...')

        response = requests.get(f'{BASE_API_URL}/api/item/list?limit={limit}&offset={offset}&folders={folderID}')
        data = response.json()

        if response.status_code != 200:
            print('Error fetching data:', response.status_code, response.text)
            break

        if 'data' not in data:
            print('Error: "data" key not found in response.')
            break

        items = data['data']

        if not items:
            print('No more items to fetch.')
            break

        if max_iterations is not None and offset >= max_iterations:
            print(f'Max iterations reached: {max_iterations}')
            break

        for item in items:  # you can add "and not item['annotation']" to exclude photo with note
            # Only get files in these extensions 'jpg', 'jpeg', 'png', 'bmp', 'webp', 'avif', 'jfif' &
            # does not have one of the following tags: 'Auto_FaceReco', 'No_FaceReco', 'Broken_FaceReco'
            undesired_tags = {'Auto_FaceReco', 'No_FaceReco', 'Broken_FaceReco'}
            if item['ext'] in ['jpg', 'jpeg', 'png', 'bmp', 'webp', 'avif', 'jfif'] and all(
                    tag not in item['tags'] for tag in undesired_tags):
                items_with_no_FaceTag.append(item)

        offset += 1
        print(f'Iteration {offset} completed. Total items to process: {len(items_with_no_FaceTag)}')

    return items_with_no_FaceTag


def get_thumbnail_path(item_id):
    response = requests.get(f'{BASE_API_URL}/api/item/thumbnail?id={item_id}')
    data = response.json()
    if response.status_code == 200 and 'data' in data:
        return data['data']
    else:
        print('Error fetching thumbnail:', response.text)
        return None


def get_item_ext(item_id):
    response = requests.get(f'{BASE_API_URL}/api/item/info?id={item_id}')
    data = response.json()
    if response.status_code == 200 and 'data' in data:
        return data['data']['ext']
    else:
        print('Error fetching extension:', response.text)
        return None


def update_item_FaceTag(item_id, new_tags=None):
    response = requests.get(f'{BASE_API_URL}/api/item/info?id={item_id}')
    data = response.json()
    if response.status_code == 200 and 'data' in data and data['data']:
        existing_tags = data["data"]['tags']
        all_tags = list(set(existing_tags + new_tags))

        data = {
            'id': item_id,
            'tags': all_tags,
        }
        response = requests.post(f'{BASE_API_URL}/api/item/update', json=data)
        if response.status_code == 200:
            print('Face Tags updated successfully for item', item_id)
        else:
            print('Error updating Face Tags:', response.text)
    else:
        print('Error fetching item:', response.text)


def create_unique_folder(base_path, prefix="New Face_"):
    """
    Creates a folder with a unique name based on the provided prefix and incrementing number.

    Args:
      base_path: The base path where the folder will be created.
      prefix: The prefix for the folder name (default: "New Face_").

    Returns:
      The path to the created folder.
    """
    num = 0
    while True:
        folder_name = f"{prefix}{num}"
        folder_path = os.path.join(base_path, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            return folder_path
        num += 1


def create_unique_image_name(folder_path, original_name):
    """
    Creates a folder with a unique name based on the provided prefix and incrementing number.

    Args:
      folder_path: The folder path where the file will be saved.
      original_name: The original name of the image without extension.

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


def are_images_identical(image_path1, image_path2, threshold):
    """
    Checks if two images are identical using pixel-by-pixel comparison.

    Args:
      image_path1 : cropped_face from cv2 (image from image_path).
      image_path2 (str): Path to the second image file (the matched image in Database).
      threshold: Threshold for pixel-by-pixel comparison.

    Returns:
      bool: True if the images are identical, False otherwise.
    """

    try:
        # Open images and handle potential errors
        image1 = cv2.imread(image_path1)
        image2 = cv2.imread(image_path2)
        if image1 is None or image2 is None:
            raise ValueError("Failed to read one or both images")

        # Check if image dimensions match (fast initial check)
        if image1.shape != image2.shape:
            print("Images have different shapes")
            return False

        # Convert to grayscale for comparison
        image1_gray = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        image2_gray = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

        # Efficient pixel-by-pixel comparison using NumPy
        difference = cv2.absdiff(image1_gray, image2_gray)
        if cv2.countNonZero(difference) <= threshold:
            return True

        # Additional check for alpha channel (if present)
        image1_pil = Image.open(image_path1)
        image2_pil = Image.open(image_path2)
        if image1_pil.mode in ("RGBA", "P") and image2_pil.mode in ("RGBA", "P"):
            alpha_difference = ImageChops.difference(image1_pil.convert("RGBA").getchannel('A'),
                                                     image2_pil.convert("RGBA").getchannel('A'))
            if alpha_difference.getbbox() is not None:  # Check for non-zero differences
                return False

        return False

    except (IOError, ValueError) as e:
        print(f"Error occurred: {e}")
        return False


def crop_face(original_image, facial_area):
    """
    Checks if two images are identical using pixel-by-pixel comparison.

    Args:
      original_image : the original image loaded by cv2.
      facial_area : the dictionary or pandas containing facial area information.

    Returns:
      cropped_face: the cropped face, ready to save.
    """
    # Get the image cropping area, Assuming image is a NumPy array
    clipped_area = clip_coordinates(facial_area, original_image.shape[1], original_image.shape[0])

    # Use clipped_area for cropping:
    cropped_face = original_image[clipped_area['y']:clipped_area['y'] + clipped_area['h'],
                                  clipped_area['x']:clipped_area['x'] + clipped_area['w']]
    return cropped_face


def face_recognition(item_id, img_path, db_path, tempo_folder, model_name, detector_backend,
                     distance_metric, expand_percentage):
    """
    Face recognition using DeepFace.
    Args:
        item_id: the Eagle id of the image
        img_path: The path to the image to find match for.
        db_path: The path to the DeepFace database to search in.
        tempo_folder: The path to the temporary folder to save the faces when same name is found and do pixel-by-pixel
                        comparison. The image will be deleted after comparison complete.
        model_name: The name of the model to use.
        detector_backend: The backend to use.
        distance_metric: The distance metric to use.
        expand_percentage: The percentage of faces to expand for cropping.

    Returns:

    """
    image_name = os.path.basename(img_path)  # Get the image name with extension
    image_name_no_ext = image_name.rsplit(".", 1)[0]  # Split from right at first dot

    try:  # Handel if face detected or not
        extracted_faces = DeepFace.extract_faces(img_path=img_path, enforce_detection=True,
                                                detector_backend=detector_backend, expand_percentage=expand_percentage)

        print(f"Face Extracted Successfully in {image_name}")

    except Exception as e:  # Handel Errors
        extracted_faces = None
        if "Face could not be detected" in str(e):  # Handel Face could not be detected
            print(f"Face could not be detected (DeepFace.extract_faces) in {image_name}")

            # Eagle add Tags:
            update_item_FaceTag(item_id, ["No_FaceReco"])
            print(f"Image Name: {image_name} | Tagged with: No_FaceReco")

        else:
            print(e)  # Handel Other Errors

    if extracted_faces:  # if extracted_faces run successfully:
        img = cv2.imread(img_path)  # Read the image

        for face in range(len(extracted_faces)):  # Search for every face in the image
            facial_area = extracted_faces[face]['facial_area']  # Get the face coordinate
            cropped_face = crop_face(img, facial_area)  # Crop the Face from original image

            try:  # Handel if face detected or not
                res = DeepFace.find(img_path=cropped_face, db_path=db_path, enforce_detection=True,
                                    model_name=model_name, detector_backend=detector_backend,
                                    distance_metric=distance_metric, expand_percentage=expand_percentage, silent=True)

            except Exception as e:  # Handel Errors
                res = None
                if "Face could not be detected" in str(e):  # Handel Face could not be detected
                    print(f"Face could not be detected (DeepFace.find) in {image_name}")
                else:
                    print(e)  # Handel Other Errors

            if res:  # if res run successfully:
                if len(res[0]['identity']) > 0:  # If face has match:
                    # Get image Full path of matched face
                    matched_image_path = res[0]['identity'][0]
                    # Get image name with Extension of matched face
                    matched_image_name = res[0]['identity'][0].split('\\')[-1]
                    # Get image name without extension
                    matched_image_name_no_ext = matched_image_name.rsplit(".", 1)[0]
                    matched_folder_path = os.path.dirname(matched_image_path)
                    # define the save path to matched folder in Database
                    matched_save_path = os.path.join(matched_folder_path, f"{image_name_no_ext}.jpg")

                    # Get folder name of matched face (Face Name)
                    if "new_faces" in matched_folder_path:
                        matched_folder_name = res[0]['identity'][0].split('\\')[3]
                        # Eagle add Tags:
                        new_tags = ["Extracted_FaceReco"]
                        update_item_FaceTag(item_id, new_tags)
                        print(f"Image Name: {image_name} | Tagged with: {new_tags}")

                    else:
                        matched_folder_name = res[0]['identity'][0].split('\\')[2]
                        # Eagle add Tags:
                        new_tags = [matched_folder_name, "Auto_FaceReco"]
                        update_item_FaceTag(item_id, new_tags)
                        print(f"Image Name: {image_name} | Tagged with: {new_tags}")

                    print(f"Image Name: {image_name} | Matched with: {matched_folder_name}")

                    # Check if the file with same name already exists
                    if os.path.exists(matched_save_path):
                        print("File with same name already exists!")

                        # save cropped face to tempo Folder:
                        tempo_file_path = os.path.join(tempo_folder, f"{image_name_no_ext}.jpg")
                        cv2.imwrite(tempo_file_path, cropped_face)

                        # Check if cropped source Face is exact match of target cropped Face
                        # (Source = img_path/tempo_file) (target = the matched image in database)
                        if are_images_identical(tempo_file_path, matched_image_path, threshold):
                            print("Images are identical, didn't save")
                        else:  # Save cropped_face/tempo_file to matched folder in Database
                            print("Images are different, Saving...")
                            # Create a unique image name and store the image path
                            unique_image_path = create_unique_image_name(matched_folder_path, image_name_no_ext)

                            try:
                                cv2.imwrite(unique_image_path, cropped_face)
                                print("Image saved successfully")
                            except Exception as e:
                                if "Assertion failed" in str(e):  # Handle file with same name already exist
                                    print("Matched image with same name in same folder is found, Image couldn't be saved")
                                else:  # Handel other Errors
                                    print(e)

                        # Remove tempo image
                        # Check if the file exists (optional but recommended)
                        if os.path.exists(tempo_file_path):
                            os.remove(tempo_file_path)
                            print(f"Tempo File '{tempo_file_path}' deleted successfully.")
                        else:
                            print(f"Tempo File '{tempo_file_path}' does not exist.")

                    else:  # Save cropped_face to matched folder in Database

                        try:
                            cv2.imwrite(matched_save_path, cropped_face)
                            print("Image saved successfully")
                        except Exception as e:
                            if "Assertion failed" in str(e):  # Handle file with same name already exist
                                print("Matched image with same name in same folder is found, Image couldn't be saved")
                            else:  # Handel other Errors
                                print(e)

                else:  # If face has No match
                    print(f"Image Name: {image_name} | No Match found!!")

                    # Save cropped_face to "New Face_{num}" in new_faces_path
                    # Create a unique folder and store the folder name path
                    unique_folder_name = create_unique_folder(new_faces_path)
                    new_image_save_path = os.path.join(unique_folder_name, f"{image_name_no_ext}.jpg")
                    cv2.imwrite(new_image_save_path, cropped_face)
                    print(f"New Face added to new_faces successfully!, to Folder: {unique_folder_name}")

                    # Eagle add Tags:
                    new_tags = ["Extracted_FaceReco"]
                    update_item_FaceTag(item_id, new_tags)
                    print(f"Image Name: {image_name} | Tagged with: {new_tags}")

# -----------------------------------------------------------


folderID = get_folderID(folderNameToProcess)
items_with_no_FaceTag = get_items_with_no_FaceTag(folderID=folderID)

for item in items_with_no_FaceTag:
    thumbnail_path = get_thumbnail_path(item['id'])

    if thumbnail_path:
        thumbnail_path = unquote(thumbnail_path)
        # print("Thumbnail path: ", thumbnail_path)
        original_image_ext = get_item_ext(item['id'])
        # print(original_image_ext)
        original_image_path = thumbnail_path.replace("_thumbnail.png", f".{original_image_ext}")
        # print("Original image path: ", original_image_path)

        try:
            face_recognition(item_id=item['id'], img_path=original_image_path, db_path=database_path, tempo_folder=tempo_folder,
                             model_name=model_name, detector_backend=detector_backend,
                             distance_metric=distance_metric, expand_percentage=expand_percentage)

        except (FileNotFoundError, SyntaxError) as e:
            print(f'Error processing file: {original_image_path} ({e})')
            # Add 'Broken_FaceReco' tag for corrupted images
            update_item_FaceTag(item['id'], new_tags=["Broken_FaceReco"])
            print(f'Tagged item {item["id"]} as "Broken_FaceReco"')
            continue

print("Face Recognition Complete")
