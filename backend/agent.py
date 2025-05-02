# backend/agent.py

import openai
import os
from dotenv import load_dotenv
from sms import send_sms
from database import save_lead_responses
from scheduler import book_appointment

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class AI_Sales_Agent:
    def process_sms(self, phone_number):
        questions = [
            "What is your budget for this project?",
            "What is your timeline for implementation?",
            "Would you like to schedule a call or site visit?"
        ]
        responses = []

        for question in questions:
            send_sms(phone_number, question)
            responses.append(f"(Placeholder) Response to: {question}")  # Placeholder for SMS reply

        save_lead_responses(phone_number, responses)
        appointment_time = book_appointment(phone_number)
        send_sms(phone_number, f"Thank you! We’ve booked your appointment on {appointment_time}")

        return {"status": "success", "scheduled": appointment_time}
