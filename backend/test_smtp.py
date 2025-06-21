import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get sender email and app password from environment variables
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')

# Recipient email (can be your own email for testing)
RECIPIENT_EMAIL = "your_personal_email@example.com"  # <--- REPLACE WITH AN EMAIL YOU CAN CHECK
TEST_SUBJECT = "SMTP Test from Free Website Wizards"
TEST_BODY = "This is a test email sent from a standalone Python script to verify SMTP login."

print(f"Testing SMTP with SENDER_EMAIL: {SENDER_EMAIL}")
print(f"Using SENDER_PASSWORD (length): {len(SENDER_PASSWORD) if SENDER_PASSWORD else 0}")

try:
    # Set up the SMTP server
    smtp_server = "smtp.gmail.com"
    smtp_port = 587  # TLS port

    print(f"Connecting to SMTP server: {smtp_server}:{smtp_port}...")
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Upgrade connection to secure TLS

    print("Attempting to log in...")
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    print("✅ Login successful!")

    # Create the email message
    msg = MIMEText(TEST_BODY)
    msg['Subject'] = TEST_SUBJECT
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL

    print(f"Sending email to {RECIPIENT_EMAIL}...")
    server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    print("✅ Email sent successfully!")

except smtplib.SMTPAuthenticationError as e:
    print(f"❌ SMTP Authentication Error: {e}")
    print("This typically means the username or app password is incorrect, or Google is blocking the login attempt.")
    print("Double-check your app password and ensure 2-Step Verification is enabled for the SENDER_EMAIL account.")
    print("You might also need to generate a *new* app password if this one was generated a while ago or on a different device.")
except Exception as e:
    print(f"❌ An unexpected error occurred: {e}")
finally:
    if 'server' in locals() and server:
        server.quit()
        print("SMTP server connection closed.")