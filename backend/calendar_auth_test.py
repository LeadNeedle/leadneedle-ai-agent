from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

# Start the OAuth flow
flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json', SCOPES)
creds = flow.run_local_server(port=0)

# Build calendar service
service = build('calendar', 'v3', credentials=creds)

# Create a test event
event = {
    'summary': 'Test Appointment',
    'description': 'Created by Lead Needle calendar integration',
    'start': {'dateTime': '2025-05-03T14:00:00', 'timeZone': 'America/New_York'},
    'end': {'dateTime': '2025-05-03T14:30:00', 'timeZone': 'America/New_York'},
}

created_event = service.events().insert(calendarId='primary', body=event).execute()
print('✅ Event created:', created_event.get('htmlLink'))
