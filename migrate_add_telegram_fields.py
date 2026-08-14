"""
migrate_add_telegram_fields.py

One-time migration: adds telegram_chat_id and telegram_link_code columns
to the existing users table, WITHOUT deleting any of your existing data.

Run this ONCE:
    python migrate_add_telegram_fields.py

Safe to run again - it checks if the columns already exist first.
"""
import sqlite3
import os
from config import Config

db_path = Config.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "")

if not os.path.exists(db_path):
    print(f"No database found at {db_path} - nothing to migrate. "
          "Just run app.py normally and the new columns will be created automatically.")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users)")
existing_columns = [row[1] for row in cursor.fetchall()]

if "telegram_chat_id" not in existing_columns:
    cursor.execute("ALTER TABLE users ADD COLUMN telegram_chat_id VARCHAR(50)")
    print("Added telegram_chat_id column.")
else:
    print("telegram_chat_id already exists - skipping.")

if "telegram_link_code" not in existing_columns:
    cursor.execute("ALTER TABLE users ADD COLUMN telegram_link_code VARCHAR(10)")
    print("Added telegram_link_code column.")
else:
    print("telegram_link_code already exists - skipping.")

conn.commit()
conn.close()
print("Migration complete. Your existing data is untouched.")
