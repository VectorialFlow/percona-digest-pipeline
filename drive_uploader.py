import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from constants import TOKEN_FILE, SERVER_FOLDERS

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    """Authenticates using an OAuth 2.0 refresh token and returns the Drive API service."""
    creds = None
    
    # Load the credentials from the token file
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If there are no valid credentials available, try to refresh them
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[Drive] Access token expired. Refreshing automatically...")
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        else:
            raise FileNotFoundError(
                f"Valid token not found at {TOKEN_FILE}. "
                "Please run 'generate_token.py' locally to generate one."
            )
            
    return build('drive', 'v3', credentials=creds)

def get_or_create_folder(service, folder_name, parent_id):
    """Checks if a folder exists within a parent folder, creates it if it doesn't."""
    query = (
        f"name='{folder_name}' and "
        f"'{parent_id}' in parents and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"trashed=false"
    )
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    
    if items:
        return items[0]['id']
    
    # If not found, create it
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

def upload_server_artifacts(server_num, date_range_folder_name, artifacts):
    """
    Handles the directory tree creation: mysql_8 -> bbdd-{server_num} -> {date_range}
    and uploads the generated artifacts. Returns the Drive link to the folder.
    """
    print(f"[Drive] Connecting to Google Drive for Server {server_num}...")
    service = get_drive_service()
    
    server_folder_id = SERVER_FOLDERS.get(str(server_num))
    if not server_folder_id:
        print(f"[Drive] ERROR: No Drive folder configured for server {server_num}")
        return None
    
    # Get or create the date range folder inside 'bbdd-X'
    date_folder_id = get_or_create_folder(service, date_range_folder_name, server_folder_id)
    
    # Upload artifacts
    for file_path in artifacts:
        if os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            print(f"[Drive] Uploading {file_name}...")
            
            file_metadata = {'name': file_name, 'parents': [date_folder_id]}
            media = MediaFileUpload(file_path, resumable=True)
            
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        else:
            print(f"[Drive] WARNING: File not found {file_path}")
            
    folder_url = f"https://drive.google.com/drive/folders/{date_folder_id}"
    print(f"[Drive] Upload complete! Available at: {folder_url}")
    return folder_url