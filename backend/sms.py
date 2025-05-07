# backend/sms.py

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(account_sid, auth_token)

def send_sms(to, message):
    try:
        sent = client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=to
        )
        print(f"✅ SMS sent to {to}: {sent.sid}")
    except Exception as e:
        print(f"❌ Failed to send SMS: {e}")
