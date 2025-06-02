import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from website import website_bp
from backend.sms import send_sms
from backend.database import insert_lead
from backend.scheduler import book_appointment
from backend.agent import AI_Sales_Agent

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))

app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.register_blueprint(website_bp)

# Google Sheets setup

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
    return client.open_by_key("1QJ91JGh16v3g8JO4A-YUCLgfhIhADSNppw0NMWjSpP4").worksheet(sheet_name)

# Email notification function

def send_notification_email(form_data, recipient="dylan@leadneedle.com"):
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = os.environ.get('SENDER_EMAIL', 'your-email@gmail.com')
        sender_password = os.environ.get('SENDER_PASSWORD', 'your-app-password')

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = "New Contact Form Submission"

        body = f"""
        New contact form submission received:

        Name: {form_data['firstName']} {form_data['lastName']}
        Email: {form_data['email']}
        Phone: {form_data['phone']}
        Service: {form_data['service']}
        Message: {form_data['message']}

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

def handle_form_submission(sheet_name, recipient):
    try:
        form_data = {
            'firstName': request.form.get('firstName'),
            'lastName': request.form.get('lastName'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'service': request.form.get('service'),
            'message': request.form.get('message'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        required_fields = ['firstName', 'lastName', 'email', 'phone', 'service', 'message']
        for field in required_fields:
            if not form_data[field]:
                flash(f'{field} is required', 'error')
                return redirect(url_for('website_bp.home'))

        sheet = get_google_sheet(sheet_name)
        row = [
            form_data['timestamp'],
            form_data['firstName'],
            form_data['lastName'],
            form_data['email'],
            form_data['phone'],
            form_data['service'],
            form_data['message']
        ]
        sheet.append_row(row)

        email_sent = send_notification_email(form_data, recipient=recipient)
        if email_sent:
            print(f"✅ Email sent to {recipient}")
        else:
            print(f"❌ Failed to send email to {recipient}")

        flash('Thank you for your message! We\'ll get back to you soon.', 'success')
        return redirect(url_for('website_bp.home'))

    except Exception as e:
        print(f"Error processing form: {e}")
        flash('There was an error submitting your form. Please try again.', 'error')
        return redirect(url_for('website_bp.home'))

@app.route('/submit', methods=['POST'])
def submit_contact_form():
    return handle_form_submission("Submissions", "dylan@leadneedle.com")

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
