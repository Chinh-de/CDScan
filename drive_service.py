import os.path
import io
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class DriveService:
    def __init__(self, credentials_path="credentials.json", token_path=None):
        self.credentials_path = credentials_path
        
        if token_path is None:
            # Hide token in AppData/CDScanner
            app_data = os.environ.get('APPDATA', os.path.expanduser("~"))
            storage_dir = Path(app_data) / "CDScanner"
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.token_path = str(storage_dir / "token.json")
        else:
            self.token_path = token_path
            
        self.service = self._authenticate()

    def _authenticate(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"Missing {self.credentials_path}. Please place it in the project root.")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        return build('drive', 'v3', credentials=creds)

    def get_folder_path(self, folder_id, max_levels=5):
        """Construct a partial path for a folder up to max_levels."""
        path_parts = []
        current_id = folder_id
        try:
            for _ in range(max_levels):
                f = self.service.files().get(
                    fileId=current_id, 
                    fields="id, name, parents"
                ).execute()
                path_parts.insert(0, f.get('name', '???'))
                parents = f.get('parents', [])
                if not parents:
                    break
                current_id = parents[0]
            if len(path_parts) == max_levels:
                path_parts.insert(0, "...")
        except Exception:
            if not path_parts: path_parts = ["Unknown"]
        return " / ".join(path_parts)

    def find_folders_by_name(self, folder_name):
        """Find folders by name and return list of {id, name}."""
        query = f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_name}' and trashed = false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        return results.get('files', [])

    def get_images_from_folder_id(self, folder_id):
        """List image files inside a specific folder ID."""
        img_query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false"
        img_results = self.service.files().list(q=img_query, fields="files(id, name, mimeType)").execute()
        return img_results.get('files', [])

    def list_images_in_folder(self, folder_name):
        """Deprecated: Use find_folders_by_name instead for disambiguation."""
        items = self.find_folders_by_name(folder_name)
        if not items:
            return []
        return self.get_images_from_folder_id(items[0]['id'])

    def download_file(self, file_id, destination_path):
        """Download a file by ID to the local path."""
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        with open(destination_path, 'wb') as f:
            f.write(fh.getvalue())

def download_images_from_drive(folder_name, local_dest="temp_raw"):
    """High-level function to download all images from a Drive folder."""
    service = DriveService()
    images = service.list_images_in_folder(folder_name)
    
    if not images:
        return []

    dest_dir = Path(local_dest)
    dest_dir.mkdir(exist_ok=True)
    
    downloaded_paths = []
    for img in images:
        local_path = dest_dir / img['name']
        service.download_file(img['id'], local_path)
        downloaded_paths.append(str(local_path))
        
    return downloaded_paths
