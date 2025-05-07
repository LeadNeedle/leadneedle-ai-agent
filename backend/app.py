# backend/app.py

import os
from flask import Flask, request, jsonify, render_template
from sms import send_sms
from database import insert_lead
from scheduler import book_appointment
from agent import AI_Sales_Agent

# Ensure Flask looks for templates in the correct folder
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

# Homepage route for website
@app.route('/')
def homepage():
    print("Homepage route hit")  # Debug for Render logs
    return render_template("index.html")

# API route for incoming SMS
@app.route('/sms', methods=['POST'])
def receive_sms():
    data = request.get_json()
    sms_text = data.get('sms_text')
    phone = data.get('phone')

    # Use AI to get responses
    sales_agent = AI_Sales_Agent()
    responses = sales_agent.process_sms(sms_text)

    # Dummy appointment time for now (could replace with smart scheduling logic)
    appointment_time = "2025-05-03 02:00 PM"

    # Save lead to DB
    insert_lead("Unknown", phone, str(responses), appointment_time)

    # Book appointment (stub)
    book_appointment(phone)

    # Send confirmation
    send_sms(phone, "Thanks! We've saved your info and booked a time.")

    return jsonify({"status": "success"})

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
