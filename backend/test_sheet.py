import gspread
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Authenticate and create token
def get_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('leadneedle_auth.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

creds = get_credentials()
client = gspread.authorize(creds)
sheet = client.open_by_key("1QJ91JGh16v3g8JO4A-YUCLgfhIhADSNppw0NMWjSpP4").worksheet("Submissions")
sheet.append_row(["Test", "Lead", "Works"])