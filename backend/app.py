import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_cors import CORS
import gspread
# Note: oauth2client.service_account is generally used for service accounts,
# but your current get_google_sheet uses pickle/Credentials for user authentication.
# Keeping the import as it's in your original file.
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv
load_dotenv()

# Assuming 'website' is a blueprint you have defined elsewhere
# from website import website_bp 
# Uncomment the line below if you have a 'website' package/module with 'website_bp'
# For now, commenting out to avoid ImportError if it's not present
# from website import website_bp 

# Assuming these are in backend subfolder relative to app.py
# If they are in the same folder as app.py, adjust the import path
try:
    from backend.sms import send_sms
    from backend.database import insert_lead
    from backend.scheduler import book_appointment
    from backend.agent import AI_Sales_Agent
except ImportError as e:
    print(f"Warning: Could not import backend modules. Ensure paths are correct: {e}")
    # Define dummy functions/classes if you want the app to run without them for now
    def send_sms(*args, **kwargs): print("Dummy send_sms called")
    def insert_lead(*args, **kwargs): print("Dummy insert_lead called")
    def book_appointment(*args, **kwargs): print("Dummy book_appointment called")
    class AI_Sales_Agent:
        def process_sms(self, *args, **kwargs): return {"status": "dummy"}


app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'static')
)

CORS(app, origins=["https://thefreewebsitewizards.com"])

app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Register blueprint if it exists and was imported successfully
# if 'website_bp' in locals():
#     app.register_blueprint(website_bp)

def get_google_sheet(sheet_name="Submissions"):
    import pickle
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    creds = None
    # Adjust path if token.pickle is not in backend/
    token_path = os.path.join(os.path.dirname(__file__), 'token.pickle')
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        else:
            # Modified to provide more helpful error for Render deployment
            raise Exception("No valid token found for Google Sheets. Ensure 'manual_auth.py' was run "
                            "locally and 'token.pickle' is available in the deployment environment, "
                            "or configure a Google Service Account for server-side auth.")

    client = gspread.authorize(creds)
    # Ensure this key is correct for your Google Sheet
    return client.open_by_key("1batVITcT526zxkc8Qdf0_AKbORnrLRB7-wHdDKhcm9M").worksheet(sheet_name)

def send_notification_email(form_data, recipient="dylan@leadneedle.com"):
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = os.environ.get('SENDER_EMAIL', 'your-email@gmail.com')
        sender_password = os.environ.get('SENDER_PASSWORD', 'your-app-password')

        if not sender_email or not sender_password:
            raise ValueError("SENDER_EMAIL or SENDER_PASSWORD environment variable not set.")

        print("[Notification Email] Using:", sender_email)
        print("[Notification Email] Password length:", len(sender_password) if sender_password else 0)

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = "New Contact Form Submission"

        body = f"""
New contact form submission received:

Name: {form_data.get('firstName', 'N/A')} {form_data.get('lastName', 'N/A')}
Email: {form_data.get('email', 'N/A')}
phoneNumber: {form_data.get('phoneNumber', 'N/A')}
Service: {form_data.get('service', 'N/A')}
Message: {form_data.get('message', 'N/A')}
Website Name: {form_data.get('websiteName', 'N/A')}
Has Website: {form_data.get('hasWebsite', 'N/A')}
Website Description: {form_data.get('websiteDescription', 'N/A')}

Submitted at: {form_data.get('timestamp', 'N/A')}
        """

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient, msg.as_string())
        server.quit()

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_confirmation_email(form_data):
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = os.environ.get('SENDER_EMAIL', 'your-email@gmail.com')
        sender_password = os.environ.get('SENDER_PASSWORD', 'your-app-password')
        recipient_email = form_data.get('email')

        if not sender_email or not sender_password:
            raise ValueError("SENDER_EMAIL or SENDER_PASSWORD environment variable not set.")
        if not recipient_email:
            print("Warning: No recipient email provided for confirmation email.")
            return False

        print("[Confirmation Email] Using:", sender_email)
        print("[Confirmation Email] Password length:", len(sender_password) if sender_password else 0)
        print(f"[Confirmation Email] Sending to: {recipient_email}")


        subject = "Your Website Application Has Been Received ✨"
        body = f"""
Hi {form_data.get('firstName', 'there')},

Thanks for applying to get your free website built by The Free Website Wizards!

We’ve received your info and our team will begin reviewing it shortly. If we have any questions, we’ll reach out directly. Otherwise, you’ll hear from us soon with the next steps.

In the meantime, feel free to check out examples of our work or share your business details with friends who might also benefit.

Your submitted website name: {form_data.get('websiteName', 'N/A')}
Your description: {form_data.get('websiteDescription', 'N/A')}

✨ Talk soon,
The Free Website Wizards
https://thefreewebsitewizards.com
        """

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()

        return True
    except Exception as e:
        print(f"Error sending confirmation email: {e}")
        return False

def handle_form_submission(sheet_name, recipient_email):
    try:
        # --- FIX: Use request.get_json() to parse JSON data from frontend ---
        data = request.get_json()
        if not data:
            raise ValueError("No JSON data received in the request body.")
        # --- END FIX ---

        form_data = {
            'firstName': data.get('firstName'),
            'lastName': data.get('lastName'), # Added for completeness if frontend sends it
            'email': data.get('email'),
            'phoneNumber': data.get('phoneNumber'),
            'websiteName': data.get('websiteName'),
            'websiteDescription': data.get('websiteDescription'),
            'hasWebsite': data.get('hasWebsite'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'service': data.get('service', 'Free Website Wizard'), # Allow frontend to specify, default if not
            'message': data.get('message', data.get('websiteDescription', '')) # Use message if present, fallback to description
        }

        sheet = get_google_sheet(sheet_name)
        row = [
            form_data['timestamp'],
            form_data.get('firstName', ''),
            form_data.get('email', ''),
            form_data.get('phoneNumber', ''),
            form_data.get('hasWebsite', ''),
            form_data.get('websiteName', ''),
            form_data.get('websiteDescription', '')
        ]
        # Ensure all values are strings before appending to Google Sheet
        row = [str(x) for x in row]
        sheet.append_row(row)
        print(f"✅ Data appended to Google Sheet '{sheet_name}'")


        # Send notification email to admin
        if not send_notification_email(form_data, recipient=recipient_email):
            print("Failed to send admin notification email.")
        else:
            print("✅ Admin notification email sent.")

        # Send confirmation email to the submitter
        if not send_confirmation_email(form_data):
            print("Failed to send user confirmation email.")
        else:
            print("✅ User confirmation email sent.")

        return jsonify({"status": "success", "message": "Form submitted successfully!"}), 200
    except Exception as e:
        print(f"Form submission error for '{sheet_name}': {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit-wizard', methods=['POST'])
def submit_wizard_form():
    return handle_form_submission("Website Submissions", "dylan@thefreewebsitewizards.com")

@app.route('/submit', methods=['POST'])
def submit_contact_form():
    # Note: If this route is also expecting JSON, it will use request.get_json() as well.
    # If it's a different form sending application/x-www-form-urlencoded,
    # you might need a separate handler or more robust content-type checking.
    return handle_form_submission("Submissions", "dylan@leadneedle.com")

@app.route('/privacy')
def redirect_privacy():
    return redirect('/privacy-policy', code=301)

@app.route('/submit-kim', methods=['POST'])
def submit_kim_contact_form():
    return handle_form_submission("Kims Fresh Start Leads", "FreshStartCleaningAug@gmail.com")

@app.route('/sms', methods=['POST'])
def receive_sms():
    # This route correctly uses request.get_json() already
    data = request.get_json()
    sms_text = data.get('sms_text')
    phone = data.get('phone')

    if not sms_text or not phone:
        return jsonify({"error": "Missing phone or sms_text"}), 400

    sales_agent = AI_Sales_Agent()
    responses = sales_agent.process_sms(phone, sms_text)

    start_time = datetime.utcnow() + timedelta(hours=1)

    insert_lead(
        name="Unknown",
        phone=phone,
        responses=str(responses),
        appointment_time=start_time.strftime("%Y-%m-%d %I:%M %p")
    )

    book_appointment(
        summary="Lead Needle Appointment",
        description=f"Auto-booked lead from {phone}",
        start_time=start_time
    )

    # Make sure send_sms is imported correctly from backend.sms
    # If it's not, this line will fail silently or loudly depending on where it's defined.
    send_sms(phone, "✅ Thanks! We've saved your info and booked your appointment.")
    return jsonify({"status": "success", "responses": responses})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)