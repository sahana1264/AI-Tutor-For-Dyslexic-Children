# create_db.py
import sqlite3

conn = sqlite3.connect("progress.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    spelling_errors INTEGER,
    reversal_errors INTEGER,
    reversed_letters TEXT,
    sentence TEXT,
    timestamp TEXT
)
""")

conn.commit()
conn.close()

print("Database created successfully.")
