import requests
import os
import json
import mimetypes
from typing import Tuple, Optional

from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload



class GDrive:
    def __init__(self):
        """
        
        """
        SCOPES = ['https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.appdata',
        'https://www.googleapis.com/auth/drive.scripts',
        'https://www.googleapis.com/auth/drive.metadata'
        ]

        SERVICE_ACCOUNT_FILE =os.path.join(os.path.dirname(__file__), 'f3e479bb8204.json')

        # Create credentials using the service account file
        self.creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        self.drive_service = build('drive', 'v3', credentials=self.creds)


    def upload_file(self, file_path: str) -> str:
        """
        Uploads a file to Google Drive.

        Args:
            file_path (str): The local path of the file to upload.
        Returns:
            url: url view of file uploaded.
        """
        file_name = os.path.basename(file_path)

        file_type = mimetypes.guess_type(file_path)[0]


        file_metadata = {
            'name': file_name,  
            'parents': ['1Hikzc5A1B0A4RFbF7qzA4TMyW5Kzjs4A']  # ID of the folder where you want to upload
        }

        media = MediaFileUpload(file_path, mimetype=file_type)

        permission = {
            'type': 'user',
            'role': 'writer', #This role grants the user edit permissions to the file
            'emailAddress': 'agraeproyectos@gmail.com',  # Replace this with your Gmail account's email address.
        }

        file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        perm = self.drive_service.permissions().create(fileId=file.get("id"), body=permission, sendNotificationEmail=None).execute()
        url = 'https://drive.google.com/file/d/{}/view?usp=sharing'.format(file.get('id'))
        return url
        
        

    



# file_path = r"D:\GeoSIG\aGrae\test\test_labels\label_A410201.pdf"



# ## Example usage
# gdrive = GDrive()
# url = gdrive.upload_file(file_name, file_path)

# print(url) 