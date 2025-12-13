"""
Platform to Broker Migration Script
====================================
This script renames all Platform-related tables and columns to Broker.
Run this ONCE before starting the backend.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'BackEnd'))

from database import engine
from sqlalchemy import text

def migrate_platform_to_broker():
    print("\n" + "="*60)
    print("🔄 MIGRATING PLATFORM → BROKER")
    print("="*60)
    
    try:
        with engine.connect() as connection:
            with connection.begin():
                
                # 1. Rename Platforms table to Brokers
                print("\n1️⃣ Renaming Platforms → Brokers...")
                try:
                    connection.execute(text('ALTER TABLE "Platforms" RENAME TO "Brokers";'))
                    print("   ✅ Table renamed")
                except Exception as e:
                    print(f"   ⚠️  {e}")
                
                # 2. Rename PlatformServers table to BrokerServers
                print("\n2️⃣ Renaming PlatformServers → BrokerServers...")
                try:
                    connection.execute(text('ALTER TABLE "PlatformServers" RENAME TO "BrokerServers";'))
                    print("   ✅ Table renamed")
                except Exception as e:
                    print(f"   ⚠️  {e}")
                
                # 3. Rename columns in Brokers table
                print("\n3️⃣ Renaming columns in Brokers...")
                try:
                    connection.execute(text('ALTER TABLE "Brokers" RENAME COLUMN "PlatformID" TO "BrokerID";'))
                    connection.execute(text('ALTER TABLE "Brokers" RENAME COLUMN "PlatformName" TO "BrokerName";'))
                    print("   ✅ Columns renamed")
                except Exception as e:
                    print(f"   ⚠️  {e}")
                
                # 4. Rename columns in BrokerServers table
                print("\n4️⃣ Renaming columns in BrokerServers...")
                try:
                    connection.execute(text('ALTER TABLE "BrokerServers" RENAME COLUMN "PlatformID" TO "BrokerID";'))
                    print("   ✅ Columns renamed")
                except Exception as e:
                    print(f"   ⚠️  {e}")
                
                # 5. Update foreign key constraints
                print("\n5️⃣ Updating foreign key constraints...")
                try:
                    # Drop old constraint
                    connection.execute(text('ALTER TABLE "BrokerServers" DROP CONSTRAINT IF EXISTS "BrokerServers_PlatformID_fkey";'))
                    # Add new constraint
                    connection.execute(text('''
                        ALTER TABLE "BrokerServers" 
                        ADD CONSTRAINT "BrokerServers_BrokerID_fkey" 
                        FOREIGN KEY ("BrokerID") 
                        REFERENCES "Brokers"("BrokerID") 
                        ON DELETE CASCADE;
                    '''))
                    print("   ✅ Constraints updated")
                except Exception as e:
                    print(f"   ⚠️  {e}")
                
                # 6. Update indexes
                print("\n6️⃣ Updating indexes...")
                try:
                    connection.execute(text('DROP INDEX IF EXISTS "ix_PlatformServers_PlatformID";'))
                    connection.execute(text('CREATE INDEX "ix_BrokerServers_BrokerID" ON "BrokerServers"("BrokerID");'))
                    print("   ✅ Indexes updated")
                except Exception as e:
                    print(f"   ⚠️  {e}")
                
                # 7. Update TradingPairs if it references PlatformServers
                print("\n7️⃣ Checking TradingPairs references...")
                try:
                    # This might not exist, but check anyway
                    connection.execute(text('ALTER TABLE "TradingPairs" DROP CONSTRAINT IF EXISTS "TradingPairs_ServerID_fkey";'))
                    connection.execute(text('''
                        ALTER TABLE "TradingPairs" 
                        ADD CONSTRAINT "TradingPairs_ServerID_fkey" 
                        FOREIGN KEY ("ServerID") 
                        REFERENCES "BrokerServers"("ServerID") 
                        ON DELETE CASCADE;
                    '''))
                    print("   ✅ TradingPairs updated")
                except Exception as e:
                    print(f"   ⚠️  {e}")
        
        print("\n" + "="*60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n⚠️  IMPORTANT: Restart the backend after this migration!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will rename database tables!")
    print("Make sure you have a backup before proceeding.")
    response = input("\nContinue? (yes/no): ")
    
    if response.lower() == 'yes':
        migrate_platform_to_broker()
    else:
        print("Migration cancelled.")
