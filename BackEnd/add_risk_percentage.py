from sqlalchemy import text
from database import engine

def add_risk_percentage_column():
    """Add RiskPercentage column to Accounts table"""
    try:
        with engine.connect() as conn:
            # Add RiskPercentage column with default value
            conn.execute(text('''
                ALTER TABLE "Accounts" 
                ADD COLUMN IF NOT EXISTS "RiskPercentage" DECIMAL(4, 2) DEFAULT 1.00 NOT NULL;
            '''))
            conn.commit()
            print("✅ Successfully added RiskPercentage column to Accounts table")
    except Exception as e:
        print(f"❌ Error updating database: {e}")

if __name__ == "__main__":
    print("Adding RiskPercentage column to Accounts table...")
    add_risk_percentage_column()
