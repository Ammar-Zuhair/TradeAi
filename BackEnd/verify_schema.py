"""
Verification script to test the new database schema.
Tests table creation, foreign keys, and indexes.
"""

from sqlalchemy import inspect, text
from database import Base, engine
from models import AssetType, Platform, PlatformServer, TradingPair, Trade

def verify_tables():
    """Verify that all tables are created"""
    print("\n" + "="*60)
    print("VERIFYING DATABASE SCHEMA")
    print("="*60)
    
    # Step 1: Create all tables
    print("\n1. Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("   ✅ Tables created successfully")
    
    # Step 2: Get table names
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("\n2. Checking tables...")
    expected_tables = ['AssetTypes', 'Platforms', 'PlatformServers', 'TradingPairs', 'Trades', 'Accounts', 'Users', 'Transactions']
    
    for table in expected_tables:
        if table in tables:
            print(f"   ✅ Table '{table}' exists")
        else:
            print(f"   ❌ Table '{table}' NOT FOUND")
    
    # Step 3: Check columns in new tables
    print("\n3. Checking table columns...")
    
    # AssetTypes
    asset_types_cols = [col['name'] for col in inspector.get_columns('AssetTypes')]
    print(f"   AssetTypes columns: {asset_types_cols}")
    
    # Platforms
    platforms_cols = [col['name'] for col in inspector.get_columns('Platforms')]
    print(f"   Platforms columns: {platforms_cols}")
    
    # PlatformServers
    servers_cols = [col['name'] for col in inspector.get_columns('PlatformServers')]
    print(f"   PlatformServers columns: {servers_cols}")
    
    # TradingPairs
    pairs_cols = [col['name'] for col in inspector.get_columns('TradingPairs')]
    print(f"   TradingPairs columns: {pairs_cols}")
    
    # Trades (updated)
    trades_cols = [col['name'] for col in inspector.get_columns('Trades')]
    print(f"   Trades columns: {trades_cols}")
    
    # Step 4: Check foreign keys
    print("\n4. Checking foreign key relationships...")
    
    # PlatformServers FKs
    servers_fks = inspector.get_foreign_keys('PlatformServers')
    print(f"   PlatformServers FKs: {len(servers_fks)} found")
    for fk in servers_fks:
        print(f"      - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
    
    # TradingPairs FKs
    pairs_fks = inspector.get_foreign_keys('TradingPairs')
    print(f"   TradingPairs FKs: {len(pairs_fks)} found")
    for fk in pairs_fks:
        print(f"      - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
    
    # Trades FKs
    trades_fks = inspector.get_foreign_keys('Trades')
    print(f"   Trades FKs: {len(trades_fks)} found")
    for fk in trades_fks:
        print(f"      - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
    
    # Step 5: Check indexes
    print("\n5. Checking indexes...")
    
    def show_indexes(table_name):
        indexes = inspector.get_indexes(table_name)
        print(f"   {table_name} indexes: {len(indexes)} found")
        for idx in indexes:
            print(f"      - {idx['name']}: {idx['column_names']}")
    
    show_indexes('PlatformServers')
    show_indexes('TradingPairs')
    show_indexes('Trades')
    
    # Step 6: Check unique constraints
    print("\n6. Checking unique constraints...")
    pairs_unique = inspector.get_unique_constraints('TradingPairs')
    print(f"   TradingPairs unique constraints: {len(pairs_unique)} found")
    for uc in pairs_unique:
        print(f"      - {uc['name']}: {uc['column_names']}")
    
    print("\n" + "="*60)
    print("✅ VERIFICATION COMPLETE")
    print("="*60 + "\n")


def run_migrations():
    """Run the migration scripts"""
    print("\n" + "="*60)
    print("RUNNING MIGRATIONS")
    print("="*60)
    
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            with connection.begin():
                # Migration for Trades - Add TradingPairID column (keep TradeAsset for migration)
                print("\n1. Adding TradingPairID column to Trades...")
                connection.execute(text('ALTER TABLE "Trades" ADD COLUMN IF NOT EXISTS "TradingPairID" INTEGER;'))
                print("   ✅ TradingPairID column added")
                
                print("\n2. Making TradeAsset nullable...")
                connection.execute(text('ALTER TABLE "Trades" ALTER COLUMN "TradeAsset" DROP NOT NULL;'))
                print("   ✅ TradeAsset is now nullable")
                
                # Add foreign key constraint
                print("\n3. Adding foreign key constraint...")
                try:
                    connection.execute(text('''
                        ALTER TABLE "Trades" 
                        ADD CONSTRAINT "fk_trades_trading_pair" 
                        FOREIGN KEY ("TradingPairID") 
                        REFERENCES "TradingPairs"("PairID") 
                        ON DELETE RESTRICT;
                    '''))
                    print("   ✅ Foreign key constraint added")
                except Exception as e:
                    print(f"   ⏭️  Foreign key constraint already exists: {e}")
                
                # Create indexes
                print("\n4. Creating indexes...")
                connection.execute(text('CREATE INDEX IF NOT EXISTS "ix_trades_trading_pair_id" ON "Trades"("TradingPairID");'))
                connection.execute(text('CREATE INDEX IF NOT EXISTS "ix_platform_servers_platform_id" ON "PlatformServers"("PlatformID");'))
                connection.execute(text('CREATE INDEX IF NOT EXISTS "ix_trading_pairs_asset_type_id" ON "TradingPairs"("AssetTypeID");'))
                connection.execute(text('CREATE INDEX IF NOT EXISTS "ix_trading_pairs_server_id" ON "TradingPairs"("ServerID");'))
                print("   ✅ All indexes created")
                
        print("\n" + "="*60)
        print("✅ MIGRATIONS COMPLETE")
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n❌ MIGRATION ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        verify_tables()
        run_migrations()
        
        print("\n" + "="*60)
        print("FINAL VERIFICATION")
        print("="*60)
        verify_tables()
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
