# backend/sms.py

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
messaging_service_sid = "MG9b56cdbfee78ab04230f455560a7382e"  # Your Messaging Service SID

client = Client(account_sid, auth_token)

def send_sms(to, message):
    try:
        sent = client.messages.create(
            body=message,
            to=to,
            messaging_service_sid=messaging_service_sid  # ✅ Replaces 'from_'
        )
        print(f"✅ SMS sent to {to}: {sent.sid}")
    except Exception as e:
        print(f"❌ Failed to send SMS to {to}: {e}")
