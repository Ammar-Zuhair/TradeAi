"""
Setup Symbol Mapping for Trading System
========================================
This script creates the necessary symbol mappings in the database
for the trading system to work correctly.
"""

import sys
import os

# Add BackEnd to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'BackEnd'))

from database import SessionLocal
from models.trading_pair import TradingPair
from models.account_symbol_mapping import AccountSymbolMapping
from models.account import Account
from models.asset_type import AssetType

def setup_symbol_mappings():
    """Create symbol mappings for all accounts"""
    db = SessionLocal()
    
    try:
        print("\n" + "="*60)
        print("🔧 SETTING UP SYMBOL MAPPINGS")
        print("="*60)
        
        # 1. Check if XAUUSDm exists in TradingPairs
        pair = db.query(TradingPair).filter(TradingPair.OurPairName == 'XAUUSDm').first()
        
        if not pair:
            print("\n❌ TradingPair 'XAUUSDm' not found!")
            print("   Creating it now...")
            
            # Get or create Gold asset type
            gold_asset = db.query(AssetType).filter(AssetType.AssetTypeName == 'Gold').first()
            if not gold_asset:
                gold_asset = AssetType(AssetTypeName='Gold')
                db.add(gold_asset)
                db.commit()
                db.refresh(gold_asset)
                print(f"   ✅ Created AssetType: Gold (ID: {gold_asset.AssetTypeID})")
            
            # Create TradingPair
            pair = TradingPair(
                OurPairName='XAUUSDm',
                PairName='XAUUSD',
                AssetTypeID=gold_asset.AssetTypeID
            )
            db.add(pair)
            db.commit()
            db.refresh(pair)
            print(f"   ✅ Created TradingPair: XAUUSDm (ID: {pair.PairID})")
        else:
            print(f"\n✅ TradingPair 'XAUUSDm' found (ID: {pair.PairID})")
        
        # 2. Get all accounts
        accounts = db.query(Account).all()
        
        if not accounts:
            print("\n❌ No accounts found in database!")
            return
        
        print(f"\n📊 Found {len(accounts)} account(s)")
        
        # 3. Create mappings for each account
        mappings_created = 0
        mappings_existing = 0
        
        for account in accounts:
            # Check if mapping already exists
            existing = db.query(AccountSymbolMapping).filter(
                AccountSymbolMapping.AccountID == account.AccountID,
                AccountSymbolMapping.TradingPairID == pair.PairID
            ).first()
            
            if existing:
                print(f"   ℹ️  Account {account.AccountLoginNumber}: Mapping already exists")
                mappings_existing += 1
                continue
            
            # Determine the actual symbol used by this account
            # You can customize this based on your broker
            account_symbol = "XAUUSD"  # Default
            
            # Create mapping
            mapping = AccountSymbolMapping(
                AccountID=account.AccountID,
                AccountSymbol=account_symbol,
                TradingPairID=pair.PairID
            )
            db.add(mapping)
            db.commit()
            
            print(f"   ✅ Account {account.AccountLoginNumber}: Created mapping ({account_symbol} → XAUUSDm)")
            mappings_created += 1
        
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        print(f"✅ Mappings created: {mappings_created}")
        print(f"ℹ️  Mappings already existed: {mappings_existing}")
        print(f"📌 Total accounts: {len(accounts)}")
        print("\n✅ Setup complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def verify_mappings():
    """Verify that all mappings are correct"""
    db = SessionLocal()
    
    try:
        print("\n" + "="*60)
        print("🔍 VERIFYING SYMBOL MAPPINGS")
        print("="*60)
        
        accounts = db.query(Account).all()
        
        for account in accounts:
            mappings = db.query(AccountSymbolMapping).filter(
                AccountSymbolMapping.AccountID == account.AccountID
            ).all()
            
            print(f"\n📊 Account {account.AccountLoginNumber}:")
            if mappings:
                for mapping in mappings:
                    pair = db.query(TradingPair).filter(
                        TradingPair.PairID == mapping.TradingPairID
                    ).first()
                    print(f"   ✅ {mapping.AccountSymbol} → {pair.OurPairName if pair else 'Unknown'}")
            else:
                print(f"   ❌ No mappings found!")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("\n🚀 Starting Symbol Mapping Setup...")
    setup_symbol_mappings()
    verify_mappings()
    print("\n✅ All done!")
