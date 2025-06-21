import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_cors import CORS
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv
load_dotenv()

from website import website_bp
from backend.sms import send_sms
from backend.database import insert_lead
from backend.scheduler import book_appointment
from backend.agent import AI_Sales_Agent

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'static')
)

CORS(app, origins=["https://thefreewebsitewizards.com"])

app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.register_blueprint(website_bp)

def get_google_sheet(sheet_name="Submissions"):
    import pickle
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    creds = None
    if os.path.exists('backend/token.pickle'):
        with open('backend/token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open('backend/token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        else:
            raise Exception("No valid token found. Run manual_auth.py first.")

    client = gspread.authorize(creds)
    return client.open_by_key("1batVITcT526zxkc8Qdf0_AKbORnrLRB7-wHdDKhcm9M").worksheet(sheet_name)

def send_notification_email(form_data, recipient="dylan@leadneedle.com"):
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = os.environ.get('SENDER_EMAIL', 'your-email@gmail.com')
        sender_password = os.environ.get('SENDER_PASSWORD', 'your-app-password')

        print("[Notification Email] Using:", sender_email)
        print("[Notification Email] Password length:", len(sender_password) if sender_password else 0)

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = "New Contact Form Submission"

        body = f"""
        New contact form submission received:

        Name: {form_data['firstName']} {form_data.get('lastName', '')}
        Email: {form_data['email']}
        phoneNumber: {form_data['phoneNumber']}
        Service: {form_data.get('service', 'N/A')}
        Message: {form_data.get('message', '')}
        Website Name: {form_data.get('websiteName', '')}
        Has Website: {form_data.get('hasWebsite', '')}
        Website Description: {form_data.get('websiteDescription', '')}

        Submitted at: {form_data['timestamp']}
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
        recipient_email = form_data['email']

        print("[Confirmation Email] Using:", sender_email)
        print("[Confirmation Email] Password length:", len(sender_password) if sender_password else 0)

        subject = "Your Website Application Has Been Received ✨"
        body = f"""
        Hi {form_data['firstName']},

        Thanks for applying to get your free website built by The Free Website Wizards!

        We’ve received your info and our team will begin reviewing it shortly. If we have any questions, we’ll reach out directly. Otherwise, you’ll hear from us soon with the next steps.

        In the meantime, feel free to check out examples of our work or share your business details with friends who might also benefit.

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
        form_data = {
            'firstName': request.form.get('firstName'),
            'email': request.form.get('email'),
            'phoneNumber': request.form.get('phoneNumber'),
            'websiteName': request.form.get('websiteName'),
            'websiteDescription': request.form.get('websiteDescription'),
            'hasWebsite': request.form.get('hasWebsite'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'service': 'Free Website Wizard',
            'message': request.form.get('websiteDescription')
        }

        sheet = get_google_sheet(sheet_name)
        row = [
            form_data['timestamp'],
            form_data['firstName'],
            form_data['email'],
            form_data['phoneNumber'],
            form_data['hasWebsite'],
            form_data['websiteName'],
            form_data['websiteDescription']
        ]
        sheet.append_row(row)

        send_notification_email(form_data, recipient=recipient_email)
        send_confirmation_email(form_data)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"{sheet_name} form error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit-wizard', methods=['POST'])
def submit_wizard_form():
    return handle_form_submission("Website Submissions", "dylan@thefreewebsitewizards.com")

@app.route('/submit', methods=['POST'])
def submit_contact_form():
    return handle_form_submission("Submissions", "dylan@leadneedle.com")

@app.route('/privacy')
def redirect_privacy():
    return redirect('/privacy-policy', code=301)

@app.route('/submit-kim', methods=['POST'])
def submit_kim_contact_form():
    return handle_form_submission("Kims Fresh Start Leads", "FreshStartCleaningAug@gmail.com")

@app.route('/sms', methods=['POST'])
def receive_sms():
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

    send_sms(phone, "✅ Thanks! We've saved your info and booked your appointment.")
    return jsonify({"status": "success", "responses": responses})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
