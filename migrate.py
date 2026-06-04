import sqlite3
import os

db_path = os.path.join("backend", "digital_crown.db")
print(f"Connecting to {db_path}...")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

try:
    cur.execute('''
    CREATE TABLE IF NOT EXISTS cabinet_settings (
        id INTEGER PRIMARY KEY,
        opening_time_morning VARCHAR(5) DEFAULT '09:00',
        closing_time_morning VARCHAR(5) DEFAULT '13:00',
        opening_time_afternoon VARCHAR(5) DEFAULT '14:00',
        closing_time_afternoon VARCHAR(5) DEFAULT '18:00',
        is_continuous BOOLEAN DEFAULT 0,
        agenda_mode VARCHAR(20) DEFAULT 'EXACT',
        use_tickets BOOLEAN DEFAULT 0
    )
    ''')
    
    cur.execute("INSERT OR IGNORE INTO cabinet_settings (id) VALUES (1)")
    
    cur.execute('''
    CREATE TABLE IF NOT EXISTS agenda_exceptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_date DATETIME NOT NULL,
        end_date DATETIME NOT NULL,
        reason VARCHAR(255) NOT NULL,
        is_holiday BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cur.execute("ALTER TABLE appointments ADD COLUMN ticket_number INTEGER;")
    print("Tables created and altered!")
except Exception as e:
    print(f"Error: {e}")

conn.commit()
conn.close()
