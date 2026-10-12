import urllib.request
import urllib.error
import shutil
from constants import NAS_URL, NAS_USER, NAS_PASS, STAGING_FILE


def fetch_nas_log(server_num):
    """Downloads the current mysql-slow.log from the NAS using Basic Auth."""
    server_url = NAS_URL.format(server_num=server_num)
    print(f"Downloading slow query log from {server_url}...")
    
    try:
        # Set up HTTP Basic Authentication
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, server_url, NAS_USER, NAS_PASS)
        auth_handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
        opener = urllib.request.build_opener(auth_handler)
        
        # Stream the download directly to the file
        with opener.open(server_url) as response, open(STAGING_FILE, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            
        print("Download complete.")
        return True
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"Failed to reach the NAS: {e.reason}")
        return False
    except Exception as e:
        print(f"An error occurred during download: {e}")
        return False