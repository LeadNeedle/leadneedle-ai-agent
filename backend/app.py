# backend/app.py

from flask import Flask, request, jsonify
from sms import send_sms
from database import insert_lead
from scheduler import book_appointment
from agent import AI_Sales_Agent

app = Flask(__name__)
sales_agent = AI_Sales_Agent()

@app.route('/sms', methods=['POST'])
def receive_sms():
    data = request.get_json()
    sms_text = data['sms_text']
    phone = data['phone']

    # Use AI to get responses
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

if __name__ == '__main__':
    app.run()
