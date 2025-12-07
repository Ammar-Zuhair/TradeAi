"""
Migration script to add TradingStrategy column to Accounts table
Run this script once to update existing database
"""

from sqlalchemy import create_engine, text
from database import DATABASE_URL
import sys

def add_trading_strategy_column():
    """Add TradingStrategy column to Accounts table"""
    
    print("\n" + "="*60)
    print("🔄 ADDING TRADING STRATEGY COLUMN TO ACCOUNTS TABLE")
    print("="*60 + "\n")
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Check if column already exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='Accounts' 
                AND column_name='TradingStrategy'
            """)
            
            result = conn.execute(check_query)
            exists = result.fetchone()
            
            if exists:
                print("⚠️  TradingStrategy column already exists!")
                print("✅ No migration needed.\n")
                return True
            
            # Add the column
            print("📊 Adding TradingStrategy column...")
            alter_query = text("""
                ALTER TABLE "Accounts" 
                ADD COLUMN "TradingStrategy" VARCHAR(20) DEFAULT 'None'
            """)
            
            conn.execute(alter_query)
            conn.commit()
            
            print("✅ TradingStrategy column added successfully!")
            
            # Verify the column was added
            verify_query = text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name='Accounts' 
                AND column_name='TradingStrategy'
            """)
            
            result = conn.execute(verify_query)
            column_info = result.fetchone()
            
            if column_info:
                print(f"\n📋 Column Details:")
                print(f"   Name: {column_info[0]}")
                print(f"   Type: {column_info[1]}")
                print(f"   Default: {column_info[2]}")
                print("\n✅ Migration completed successfully!\n")
                return True
            else:
                print("❌ Failed to verify column creation")
                return False
                
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🚀 Starting migration...")
    success = add_trading_strategy_column()
    
    if success:
        print("="*60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\n📝 Next Steps:")
        print("   1. Restart your FastAPI server")
        print("   2. Test creating/updating accounts with TradingStrategy")
        print("   3. Update frontend to include strategy selector\n")
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ MIGRATION FAILED")
        print("="*60)
        print("\n⚠️  Please check the error messages above")
        print("   and fix any issues before retrying.\n")
        sys.exit(1)
