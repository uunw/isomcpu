"""
Script to apply schema changes directly to the database.
1. Add completedAt to repairs_request
2. Create repair_status_logs table
Run with: uv run python scripts/db_fix.py
"""
import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine

def apply_fix():
    with engine.connect() as conn:
        print("🛠️ Applying Database Schema Fix...")
        
        # 1. Add completedAt column if it doesn't exist
        try:
            conn.execute(text("ALTER TABLE repairs_request ADD COLUMN IF NOT EXISTS \"completedAt\" TIMESTAMP;"))
            print("✅ Column 'completedAt' checked/added to 'repairs_request'")
        except Exception as e:
            print(f"⚠️ Error adding column: {e}")

        # 2. Create repair_status_logs table
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS repair_status_logs (
                    id SERIAL PRIMARY KEY,
                    "repairRequestId" INTEGER REFERENCES repairs_request(id),
                    status VARCHAR NOT NULL,
                    "changedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    "changedBy" INTEGER REFERENCES technicians(id),
                    note VARCHAR
                );
            """))
            print("✅ Table 'repair_status_logs' checked/created")
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            
        conn.commit()
        print("✨ Database fix applied successfully!")

if __name__ == "__main__":
    apply_fix()
