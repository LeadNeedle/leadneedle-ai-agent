# backend/database.py

import sqlite3
import json

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS leads (
                                lead_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                lead_name TEXT,
                                lead_phone TEXT,
                                qualification_responses TEXT,
                                appointment_date TEXT
                                )''')
        self.conn.commit()

    def insert_lead(self, lead_name, lead_phone, qualification_responses, appointment_date):
        self.cursor.execute('''INSERT INTO leads (lead_name, lead_phone, qualification_responses, appointment_date)
                                VALUES (?, ?, ?, ?)''', (lead_name, lead_phone, qualification_responses, appointment_date))
        self.conn.commit()

    def get_lead_by_id(self, lead_id):
        self.cursor.execute('''SELECT * FROM leads WHERE lead_id = ?''', (lead_id,))
        return self.cursor.fetchone()

    def get_all_leads(self):
        self.cursor.execute('''SELECT * FROM leads''')
        return self.cursor.fetchall()

    def close_connection(self):
        self.conn.close()

# ✅ Used by agent.py
def save_lead_responses(lead_phone, responses):
    db = Database("leads.db")
    db.create_table()

    lead_name = "Unknown"
    appointment_date = "TBD"
    response_text = json.dumps(responses, indent=2)

    db.insert_lead(lead_name, lead_phone, response_text, appointment_date)
    db.close_connection()

    print(f"✅ Lead data saved to SQLite for {lead_phone}")

# ✅ Used by app.py
def insert_lead(lead_name, lead_phone, responses, appointment_date):
    db = Database("leads.db")
    db.create_table()

    response_text = json.dumps(responses, indent=2)
    db.insert_lead(lead_name, lead_phone, response_text, appointment_date)
    db.close_connection()

    print(f"✅ insert_lead saved {lead_name} to DB")
