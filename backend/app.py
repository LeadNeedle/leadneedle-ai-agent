# backend/app.py

from flask import Flask, request, jsonify
from sms import send_sms, receive_sms
from database import save_lead_data
from scheduler import book_appointment


app = Flask(__name__)
sales_agent = AI_Sales_Agent()

@app.route('/sms', methods=['POST'])
def receive_sms():
    data = request.get_json()
    sms_text = data['sms_text']
    response = sales_agent.process_sms(sms_text)
    return jsonify(response)

if __name__ == '__main__':
    app.run()