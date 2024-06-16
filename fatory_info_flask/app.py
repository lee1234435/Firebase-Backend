import os
import requests
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
from firebase_admin import firestore

PROJECT_ID = "factory-info-a8045"
DB_IMG_DIR = "factory-info-a8045.appspot.com/images"

cred = credentials.Certificate('factory-info-a8045-firebase-adminsdk-e52rt-53ce709c19.json')
default_app = firebase_admin.initialize_app(cred, {'storageBucket': f"{PROJECT_ID}.appspot.com"})

db = firestore.client()
bucket = storage.bucket()

collection_name = 'factory_info'
local_directory = 'images'

def make_blob_public_and_get_url(blob):

    # 파일이 존재하는지 확인
    if not blob.exists():
        print("The specified file does not exist.")
        return None

    # 파일을 공개로 설정
    blob.make_public()

    # 공개 URL 가져오기
    public_url = blob.public_url
    return public_url

def download_image(url, local_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(local_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"Image downloaded and saved to {local_path}")
    else:
        print("Failed to download the image")
        
def download_all_images_from_bucket(local_dir):
    blobs = bucket.list_blobs(prefix='images/')
    
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    
    for blob in blobs:
        if blob.name.endswith('/'):
            # This is a directory, skip it
            continue
        
        print(f"Processing {blob.name}")
        public_url = make_blob_public_and_get_url(blob)
        local_path = os.path.join(local_dir, os.path.basename(blob.name))
        download_image(public_url, local_path)
        
        
local_directory = 'images'
download_all_images_from_bucket(local_directory)
