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
def get_google_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('backend/leadneedle_auth.json', scope)
    client = gspread.authorize(creds)
    sh = client.open("Lead Needle Contacts").worksheet("Submissions")
    return sh

# Email notification function
def send_notification_email(form_data):
    try:
        # Email configuration - you'll need to set these environment variables
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = os.environ.get('SENDER_EMAIL', 'your-email@gmail.com')
        sender_password = os.environ.get('SENDER_PASSWORD', 'your-app-password')
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = "dylan@leadneedle.com"
        msg['Subject'] = "New Contact Form Submission on Lead Needle"
        
        # Email body
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
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, "dylan@leadneedle.com", text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route('/submit', methods=['POST'])
def submit_contact_form():
    try:
        # Extract form data
        form_data = {
            'firstName': request.form.get('firstName'),
            'lastName': request.form.get('lastName'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'service': request.form.get('service'),
            'message': request.form.get('message'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'email', 'phone', 'service', 'message']
        for field in required_fields:
            if not form_data[field]:
                flash(f'{field} is required', 'error')
                return redirect(url_for('website_bp.home'))
        
        # Add to Google Sheets
        try:
            sheet = get_google_sheet()
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
        except Exception as e:
            print(f"Error adding to Google Sheets: {e}")
            flash('There was an error submitting your form. Please try again.', 'error')
            return redirect(url_for('website_bp.home'))
        
        # Send notification email
        email_sent = send_notification_email(form_data)
        if not email_sent:
            print("Warning: Email notification failed to send")
        
        # Success message
        flash('Thank you for your message! We\'ll get back to you soon.', 'success')
        return redirect(url_for('website_bp.home'))
        
    except Exception as e:
        print(f"Error processing form: {e}")
        flash('There was an error submitting your form. Please try again.', 'error')
        return redirect(url_for('website_bp.home'))

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
