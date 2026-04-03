import sys
import os

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.database import engine
from sqlalchemy import text

def update_db():
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE pharmacy_walkin_sales ADD COLUMN IF NOT EXISTS walkin_age VARCHAR(10);"))
        conn.execute(text("ALTER TABLE pharmacy_walkin_sales ADD COLUMN IF NOT EXISTS walkin_gender VARCHAR(20);"))
        conn.execute(text("ALTER TABLE pharmacy_walkin_sales ADD COLUMN IF NOT EXISTS walkin_address VARCHAR(500);"))
        conn.execute(text("ALTER TABLE pharmacy_walkin_sales ADD COLUMN IF NOT EXISTS prescriber_name VARCHAR(200);"))
        conn.commit()
    print("Database altered successfully.")

if __name__ == "__main__":
    update_db()
