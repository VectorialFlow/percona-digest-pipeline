import os
from google_auth_oauthlib.flow import InstalledAppFlow

# The scope for uploading and managing files created by this app
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def main():
    if not os.path.exists('credentials.json'):
        print("Please download your OAuth client ID as 'credentials.json' and place it here.")
        return

    # This opens the browser for you to log in
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    # Save the credentials (including the refresh token) for the unattended script
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    
    print("Success! 'token.json' has been generated. Your unattended script will use this.")

if __name__ == '__main__':
    main()