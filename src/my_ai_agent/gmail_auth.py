import os.path
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from my_ai_agent.settings import PROJECT_ROOT

TOKEN_PATH = str(PROJECT_ROOT / "token.json")
CREDENTIALS_PATH = str(PROJECT_ROOT / "credentials.json")

# compose: create drafts and send; readonly: list, search and read mail.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def load_credentials() -> Credentials:
    creds = None
    if os.path.exists(TOKEN_PATH):
        # Load without passing SCOPES: that would overwrite the scopes stored in the
        # file and hide a token that was granted fewer permissions than we now need.
        creds = Credentials.from_authorized_user_file(TOKEN_PATH)
        if not creds.has_scopes(SCOPES):
            creds = None  # older token (e.g. send-only): sign in again for new scopes

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            creds = None  # refresh token revoked or expired: sign in again
    else:
        creds = None

    if creds is None:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=8080)

    with open(TOKEN_PATH, "w") as token:
        token.write(creds.to_json())
    return creds


def get_gmail_service():
    return build("gmail", "v1", credentials=load_credentials())
