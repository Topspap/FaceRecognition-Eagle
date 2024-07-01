# FaceRecognition-Eagle
A Python Script that preform FaceRecognition to Eagle Library and tag matched face with their face name based on your Database and add new faces to sub folder called [new_faces]

# Pre Requists:
1. Dowload the scripts "FaceRecognition-Eagle V1.0_Stable" and "ConvertToFacesForDB_V1.0_Stable"
2. Install the requirements in "requirements.txt"
3. Create the following folders in the same location of the scripts: "my_db", (Optional): "convertToFaces_input" & "convertedFaces_output"
![image](https://github.com/Topspap/FaceRecognition-Eagle/assets/30016184/6359c084-1221-4f5e-ac22-4cfed18337d0)
5. Make sure the folder "my_db" have at least on Folder with a person photo. as in the photo:
![image](https://github.com/Topspap/FaceRecognition-Eagle/assets/30016184/02033add-71ab-4a54-a714-244002981ae5)
6. Create a Folder named "FaceReco_Process" in Eagle library and add the photos inside it to be processed.
![image](https://github.com/Topspap/FaceRecognition-Eagle/assets/30016184/c9679efa-590c-4356-8368-46c8646b2f51)
8. Make sure Eagle is open with the library you want to perform FaceRecognition on.

# How "FaceRecognition-Eagle V1.0_Stable" Script work
1. The script will look in a folder named "FaceReco_Process" in your eagle library and search for all photos in this format ('jpg', 'jpeg', 'png', 'bmp', 'webp', 'avif', 'jfif') and doesn't have these tags ('Auto_FaceReco', 'No_FaceReco', 'Broken_FaceReco')
2. Then the script will create a file in "my_db" folder with the extension .pkl, this file will contain a representation of all the faces in the database "my_db" to make matching process faster. (this fill will be updated automatically every time a face is added to the database)
3. Then the script will go through each photo(in Step 1) and extract all the faces in that photo.
4. Then for every face in the photo will performe a scan in the Database folder "my_db" to find a match.
5. If a match is found: the photo will be taged with the folder name of the matched face and 'Auto_FaceReco' tag (to be avoided the next time you run the script). Then the extracted face from the photo will be added to the database in the same folder of the matched face (to improve the face detection for later search).
6. If there is not match: the photo will be taged with 'Extracted_FaceReco', then the extracted face will be added to the Database "my_db" but in side a sub folder called "[new_faces]" E.g.: .\my_db\[new_faces]\New Face_{number}
7. then for the next photo if it found a match with a face in "[new_faces]" it will be added to the same folder and tagged with 'Extracted_FaceReco' only. (so later you can move the New Face_{number} out of [new_faces] folder and place it in "my_db" and give that folder the person name, and the next time you run the script the matched photos will be tagged with the folder name "Person Name")
8. If the photo has no face: it will be tagged with 'No_FaceReco' to be avoided the next time you run the script.

Note:

• The first time you run the script make sure that "my_db" contain at least one folder with a photo inside it.

• After the script is done you need to "Empty cache and reload" to see the updated result(Don't know why), as in the screenshot:
![image](https://github.com/Topspap/FaceRecognition-Eagle/assets/30016184/8be173c8-b800-4464-9d2c-42c066ab2aa0)

• To create a database of cropped faces from photos see "ConvertToFacesForDB_V1.0_Stable" script explanation below.

# How "ConvertToFacesForDB_V1.0_Stable" Script work
1. The script will go through every photo (including sub-folders) in "convertToFaces_input".
2. Then for each photo it will extract all faces and save them exactly in the same folder structure but in "convertedFaces_output".
3. Thats it.
4. then you can use these faces and add them to your "my_db" with a folder named of the person face.

Note:

• If the photo has multiple different persons (Faces) make sure to seperate them accordingly before giving it to the "my_db" databse, to avoid wrong matches.

# Result after running the Script one time:
![image](https://github.com/Topspap/FaceRecognition-Eagle/assets/30016184/20ea5ea6-391d-41e1-b5d4-2798014916d6)
![image](https://github.com/Topspap/FaceRecognition-Eagle/assets/30016184/0458a6c9-bfad-4d83-b6aa-f04c8d5deeb9)

"convertToFaces_input"
![image](https://github.com/Topspap/FaceRecognition-Eagle/assets/30016184/8e3307f2-f31c-45c5-ba1f-c669837443ed)

"convertedFaces_output"
![image](https://github.com/Topspap/FaceRecognition-Eagle/assets/30016184/94b15226-d82c-4d7f-a468-ddb899a1daa8)

-------------------------------------------------------------------
If you have any further question please contact me on Discord Eagle Server "https://discord.gg/w49Qjug6" my name is topspap
