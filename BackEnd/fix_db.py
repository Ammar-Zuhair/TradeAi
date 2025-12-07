from database import engine
from sqlalchemy import text

def fix_database():
    try:
        with engine.connect() as conn:
            # Alter the column type to BIGINT
            conn.execute(text('ALTER TABLE "Users" ALTER COLUMN "UserIDCardrNumber" TYPE BIGINT;'))
            conn.commit()
            print("✅ Successfully altered UserIDCardrNumber to BIGINT")
    except Exception as e:
        print(f"❌ Error updating database: {e}")

if __name__ == "__main__":
    fix_database()
