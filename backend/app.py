# backend/app.py

import os
import sys
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template

# Add root to sys.path so we can import from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from website import website_bp
from sms import send_sms
from database import insert_lead
from scheduler import book_appointment
from agent import AI_Sales_Agent

# Create the Flask app
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))

# Register website blueprint
app.register_blueprint(website_bp)

@app.route('/sms', methods=['POST'])
def receive_sms():
    data = request.get_json()

    sms_text = data.get('sms_text')
    phone = data.get('phone')

    if not sms_text or not phone:
        return jsonify({"error": "Missing phone or sms_text"}), 400

    sales_agent = AI_Sales_Agent()
    responses = sales_agent.process_sms(sms_text)

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

    send_sms(phone, "✅ Thanks! We’ve saved your info and booked your appointment.")

    return jsonify({"status": "success", "responses": responses})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
