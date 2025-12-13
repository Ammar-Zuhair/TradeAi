"""
Add AccountName Column to Database
===================================
This script adds the AccountName column to the Accounts table.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'BackEnd'))

from database import engine
from sqlalchemy import text

def add_account_name_column():
    print("\n" + "="*60)
    print("🔧 ADDING AccountName COLUMN")
    print("="*60)
    
    try:
        with engine.connect() as connection:
            with connection.begin():
                # Add AccountName column
                print("\n📝 Adding AccountName column...")
                connection.execute(text('''
                    ALTER TABLE "Accounts" 
                    ADD COLUMN IF NOT EXISTS "AccountName" VARCHAR(100);
                '''))
                
                print("✅ AccountName column added successfully!")
                
                # Optional: Set default names for existing accounts
                print("\n📝 Setting default names for existing accounts...")
                connection.execute(text('''
                    UPDATE "Accounts" 
                    SET "AccountName" = 'Account ' || "AccountLoginNumber"::TEXT
                    WHERE "AccountName" IS NULL;
                '''))
                
                print("✅ Default names set successfully!")
                
        print("\n" + "="*60)
        print("✅ Migration completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_account_name_column()
