import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

print("✅ Scheduler script started")

SCOPES = ['https://www.googleapis.com/auth/calendar']

def book_appointment(summary="Lead Needle Appointment", description="Qualified lead auto-booked.", start_time=None, duration_minutes=30):
    try:
        creds = None

        # Load saved credentials
        if os.path.exists('token.json'):
            print("🔐 Loading saved credentials from token.json")
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        # If no valid credentials, prompt login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired credentials")
                creds.refresh(Request())
            else:
                print("🧠 Prompting Google OAuth login...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials for future use
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
                print("💾 Credentials saved to token.json")

        service = build('calendar', 'v3', credentials=creds)
        print("📡 Google Calendar API client initialized")

        # Set default start time if none provided
        if not start_time:
            start_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

        end_time = start_time + datetime.timedelta(minutes=duration_minutes)

        print(f"🕒 Booking event from {start_time.isoformat()} to {end_time.isoformat()}")

        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat() + 'Z',
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat() + 'Z',
                'timeZone': 'UTC',
            },
        }

        print("📅 Sending event to Google Calendar...")
        response = service.events().insert(calendarId='primary', body=event).execute()
        print("✅ Event created successfully:")
        print(response)
        print(f"✅ Event link: {response.get('htmlLink')}")

    except Exception as e:
        print(f"❌ ERROR: {e}")

# Run directly
if __name__ == "__main__":
    book_appointment()
