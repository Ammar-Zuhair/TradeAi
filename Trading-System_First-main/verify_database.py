"""
Database Schema Verification Script
=====================================
This script checks if all model fields exist in the database.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'BackEnd'))

from database import engine
from sqlalchemy import text, inspect

def verify_database_schema():
    print("\n" + "="*60)
    print("🔍 DATABASE SCHEMA VERIFICATION")
    print("="*60)
    
    inspector = inspect(engine)
    
    # Expected schema
    expected_schema = {
        'Accounts': [
            'AccountID', 'AccountName', 'UserID', 'AccountType', 'ServerID',
            'AccountBalance', 'AccountCreationDate', 'AccountLoginNumber',
            'AccountLoginPassword', 'RiskPercentage', 'TradingStrategy'
        ],
        'Trades': [
            'TradeID', 'AccountID', 'TradeType', 'TradingPairID', 'TradeAsset',
            'TradeLotsize', 'TradeOpenPrice', 'TradeOpenTime', 'TradeClosePrice',
            'TradeCloseTime', 'TradeStatus', 'TradeProfitLose'
        ],
        'Transactions': [
            'TransactionID', 'AccountID', 'TransactionType', 'TransactionAmount',
            'TransactionDate', 'TransactionStatus'
        ],
        'Users': [
            'UserID', 'UserName', 'UserEmail', 'UserPassword', 'UserPhone',
            'UserCreationDate', 'PushToken', 'IsNotificationsEnabled'
        ],
        'Platforms': [
            'PlatformID', 'PlatformName'
        ],
        'PlatformServers': [
            'ServerID', 'PlatformID', 'ServerName'
        ],
        'AssetTypes': [
            'AssetTypeID', 'AssetTypeName'
        ],
        'TradingPairs': [
            'PairID', 'AssetTypeID', 'ServerID', 'OurPairName', 'PairName'
        ],
        'AccountSymbolMappings': [
            'MappingID', 'AccountID', 'TradingPairID', 'AccountSymbol'
        ]
    }
    
    all_good = True
    
    for table_name, expected_columns in expected_schema.items():
        print(f"\n📊 Table: {table_name}")
        
        # Check if table exists
        if table_name not in inspector.get_table_names():
            print(f"   ❌ Table does not exist!")
            all_good = False
            continue
        
        # Get actual columns
        actual_columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        # Check for missing columns
        missing = set(expected_columns) - set(actual_columns)
        extra = set(actual_columns) - set(expected_columns)
        
        if missing:
            print(f"   ❌ Missing columns: {', '.join(missing)}")
            all_good = False
        
        if extra:
            print(f"   ⚠️  Extra columns: {', '.join(extra)}")
        
        if not missing and not extra:
            print(f"   ✅ All columns present ({len(actual_columns)} columns)")
        elif not missing:
            print(f"   ✅ All required columns present")
    
    print("\n" + "="*60)
    if all_good:
        print("✅ DATABASE SCHEMA IS COMPLETE!")
    else:
        print("❌ DATABASE SCHEMA HAS ISSUES - CHECK ABOVE")
    print("="*60)

if __name__ == "__main__":
    verify_database_schema()
