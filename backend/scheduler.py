# backend/scheduler.py

import datetime

def book_appointment(lead_phone):
    # Simulate booking an appointment 2 days from now at 2 PM
    appointment_time = (datetime.datetime.now() + datetime.timedelta(days=2)).replace(hour=14, minute=0)
    print(f"📅 Appointment booked for {lead_phone} on {appointment_time.strftime('%Y-%m-%d %I:%M %p')}")
    return appointment_time
