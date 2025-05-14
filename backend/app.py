# backend/app.py

import os
from flask import Flask, request, jsonify, render_template
from sms import send_sms
from database import insert_lead
from scheduler import book_appointment
from agent import AI_Sales_Agent
from datetime import datetime, timedelta

# Initialize Flask
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

# Homepage route (for Render + browser)
@app.route('/')
def homepage():
    print("✅ Homepage route accessed")  # Helpful log for debugging
    return render_template("index.html")

# API route to handle incoming SMS and trigger agent logic
@app.route('/sms', methods=['POST'])
def receive_sms():
    data = request.get_json()

    sms_text = data.get('sms_text')
    phone = data.get('phone')

    if not sms_text or not phone:
        return jsonify({"error": "Missing phone or sms_text"}), 400

    # Run message through AI agent
    sales_agent = AI_Sales_Agent()
    responses = sales_agent.process_sms(sms_text)

    # Pick a booking time 1 hour from now
    start_time = datetime.utcnow() + timedelta(hours=1)

    # Save to DB
    insert_lead(name="Unknown", phone=phone, responses=str(responses), appointment_time=start_time.strftime("%Y-%m-%d %I:%M %p"))

    # Book appointment on calendar
    book_appointment(
        summary="Lead Needle Appointment",
        description=f"Auto-booked lead from {phone}",
        start_time=start_time
    )

    # Confirm to user
    send_sms(phone, "✅ Thanks! We’ve saved your info and booked your appointment.")

    return jsonify({"status": "success", "responses": responses})

# Entry point for local dev or Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
