# backend/agent.py

from flask import Flask, request
from openai import OpenAI
from sms import send_sms
from database import save_lead_responses
from scheduler import book_appointment

app = Flask(__name__)
client = OpenAI(api_key="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")

@app.route('/qualify_lead', methods=['POST'])
def qualify_lead():
    lead_phone = request.json.get('phone')
    if not lead_phone:
        return {"error": "Missing phone"}, 400

    send_sms(lead_phone, "👋 Hi! Let's get started with a few quick questions.")

    questions = [
        "What is your budget for this project?",
        "What is your timeline for implementation?"
    ]
    responses = []

    for question in questions:
        # Send question to user
        send_sms(lead_phone, question)

        # Simulate AI-generated response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You're acting as a curious sales agent."},
                {"role": "user", "content": question}
            ],
            temperature=0.7
        )
        answer = response.choices[0].message.content.strip()
        responses.append(f"{question} — {answer}")

    save_lead_responses(lead_phone, responses)
    book_appointment(lead_phone)
    send_sms(lead_phone, "📅 Thanks! Your appointment is booked. We'll follow up soon.")

    return {"status": "success"}, 200

if __name__ == '__main__':
    app.run()
