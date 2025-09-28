import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"]


def get_gmail_service():
    creds = None

    if os.path.exists("token.pickle"): 
        with open("token.pickle", 'rb') as token:
            creds = pickle.load(token)
    
    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=8080)
        with open("token.pickle", 'wb') as token:
            pickle.dump(creds, token)


    return build("gmail", "v1", credentials=creds)

  

