# backend/agent.py

import openai
import os
import json
from dotenv import load_dotenv
from sms import send_sms
from database import save_lead_responses
from scheduler import book_appointment

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


class AI_Sales_Agent:
    def __init__(self):
        self.system_prompt = """
You are Lead Needle, a helpful and efficient AI sales assistant designed to qualify leads and schedule jobs for home service businesses. You operate strictly via SMS.

Your goal is to:
1. Greet and guide the customer through the sales process.
2. Ask questions to qualify the job.
3. Call appropriate tools to quote or schedule the job.
4. Confirm details with the customer clearly before any booking.
5. Keep conversations short, friendly, and professional.

RULES:
- Never ask more than 1 question at a time.
- NEVER make assumptions. If info is missing, ask politely.
- Use tools whenever appropriate (quote, schedule, reply, store).
- Format tool calls as strict JSON and do NOT include any extra commentary.
- NEVER say you are an AI or assistant unless asked.
- When quoting, ask for square footage or job size if not provided.
- Use the customer’s tone. If they are formal, be formal. If casual, match it subtly.

TOOL CALL FORMAT:
Always return tool calls in this format:

```json
{
  "tool": "tool_name",
  "parameters": {
    "key": "value"
  }
}
Only return one tool call at a time. If no tool is required, reply in plain English.
"""

python
Copy
Edit
def process_sms(self, phone_number, incoming_sms):
    # Build message history
    messages = [
        {"role": "system", "content": self.system_prompt},
        {"role": "user", "content": incoming_sms}
    ]

    try:
        # Send to OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=0.5
        )

        reply = response.choices[0].message.content.strip()

        # Try to parse it as a tool call
        if reply.startswith("{") and reply.endswith("}"):
            tool_call = json.loads(reply)
            return self.handle_tool(tool_call, phone_number)

        # Fallback: plain SMS reply
        send_sms(phone_number, reply)
        save_lead_responses(phone_number, [incoming_sms, reply])
        return {"status": "message_sent", "reply": reply}

    except Exception as e:
        send_sms(phone_number, "Sorry, something went wrong.")
        return {"status": "error", "message": str(e)}

def handle_tool(self, tool_call, phone_number):
    tool = tool_call.get("tool")
    params = tool_call.get("parameters", {})

    if tool == "calendar_event":
        time = params.get("time", "TBD")
        book_appointment(phone_number)  # Your real logic may use `params`
        send_sms(phone_number, f"Appointment booked for {time}.")
        return {"status": "appointment_booked", "time": time}

    elif tool == "quote_lead":
        sqft = params.get("square_footage", 0)
        job_type = params.get("job_type", "general service")
        estimated_price = self.calculate_quote(job_type, sqft)
        send_sms(phone_number, f"Estimated quote for {job_type}: ${estimated_price}")
        return {"status": "quote_sent", "amount": estimated_price}

    elif tool == "sms_reply":
        message = params.get("message", "")
        send_sms(phone_number, message)
        return {"status": "message_sent"}

    elif tool == "store_lead":
        save_lead_responses(phone_number, params)
        return {"status": "lead_saved"}

    else:
        send_sms(phone_number, "I didn't understand the request.")
        return {"status": "unknown_tool"}

def calculate_quote(self, job_type, square_footage):
    base_rate = 0.15  # Example: $0.15 per sq ft
    return round(square_footage * base_rate, 2)
yaml
Copy
Edit

---

### 🔧 To Complete the Setup

1. **In your Flask route**, call it like:
```python
agent = AI_Sales_Agent()
result = agent.process_sms(phone_number, sms_text)