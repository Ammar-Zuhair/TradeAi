"""
Setup Symbol Mapping for Trading System
========================================
This script creates the necessary symbol mappings in the database
for the trading system to work correctly.
"""

import sys
import os

import MetaTrader5 as mt5
from security import decrypt

def find_best_symbol(wanted_asset_name):
    """
    Find the best matching symbol in MT5 for a given asset name.
    """
    # 1. Try exact known variations first (Priority list)
    variations = [
        wanted_asset_name,                 # e.g. "XAUUSD"
        "GOLD", "Gold",                    # Common names
        f"{wanted_asset_name}m",           # Suffix m
        f"{wanted_asset_name}.m",          # Suffix .m
        f"{wanted_asset_name}pro",         # Suffix pro
        f"{wanted_asset_name}_pro",        # Suffix _pro
        f"{wanted_asset_name}ecn",         # Suffix ecn
        f"{wanted_asset_name}.a",          # Suffix .a
        f"{wanted_asset_name}+",           # Suffix +
    ]
    
    # Check if any variation exists exactly
    for symbol in variations:
        info = mt5.symbol_info(symbol)
        if info:
            return symbol
            
    # 2. If not found, search all symbols containing the name
    # Search for "XAU" or "GOLD"
    keywords = ["XAU", "GOLD"]
    all_symbols = mt5.symbols_get()
    
    if all_symbols:
        for s in all_symbols:
            s_name = s.name.upper()
            for kw in keywords:
                if kw in s_name:
                    # Found a candidate, return the first one found (usually the simplest)
                    # Ideally we would rank them, but first match is often sufficient if loop is ordered
                    return s.name
                    
    return None

def setup_symbol_mappings():
    """Create symbol mappings for all accounts"""
    db = SessionLocal()
    
    try:
        print("\n" + "="*60)
        print("🔧 SETTING UP SYMBOL MAPPINGS")
        print("="*60)
        
        # 1. Check if XAUUSDm exists in TradingPairs
        # We rename it to 'GOLD' internally for clarity, or keep XAUUSDm as OurPairName
        target_pair_name = 'XAUUSDm' 
        pair = db.query(TradingPair).filter(TradingPair.PairNameForSearch == target_pair_name).first()
        
        if not pair:
            print(f"\n❌ TradingPair '{target_pair_name}' not found!")
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
                PairNameForSearch=target_pair_name,
                AssetTypeID=gold_asset.AssetTypeID
            )
            db.add(pair)
            db.commit()
            db.refresh(pair)
            print(f"   ✅ Created TradingPair: {target_pair_name} (ID: {pair.PairID})")
        else:
            print(f"\n✅ TradingPair '{target_pair_name}' found (ID: {pair.PairID})")
        
        # 2. Get all accounts
        accounts = db.query(Account).all()
        
        if not accounts:
            print("\n❌ No accounts found in database!")
            return
        
        print(f"\n📊 Found {len(accounts)} account(s)")
        
        # 3. Create mappings for each account
        mappings_created = 0
        mappings_updated = 0
        
        for account in accounts:
            print(f"\n🔹 Processing Account {account.AccountLoginNumber}...")
            
            # 3.1 Connect to MT5 to find symbol
            try:
                password = decrypt(account.AccountLoginPassword)
                if not mt5.initialize(login=account.AccountLoginNumber, password=password, server=account.AccountLoginServer):
                    print(f"   ❌ Failed to connect to MT5: {mt5.last_error()}")
                    continue
                
                print(f"   ✅ Connected to MT5")
                
                # 3.2 Find best symbol for XAUUSD/GOLD
                # We assume we are looking for Gold for now as per 'XAUUSDm' logic
                detected_symbol = find_best_symbol("XAUUSD")
                
                mt5.shutdown() # Close connection
                
                if not detected_symbol:
                    print(f"   ⚠️ Could not detect Gold symbol automatically. Using default 'XAUUSD'.")
                    detected_symbol = "XAUUSD"
                else:
                    print(f"   ✅ Detected Symbol: {detected_symbol}")
                    
            except Exception as e:
                print(f"   ❌ Error connecting/detecting: {e}")
                detected_symbol = "XAUUSD" # Fallback
            
            # 3.3 Update/Create Mapping
            existing = db.query(AccountSymbolMapping).filter(
                AccountSymbolMapping.AccountID == account.AccountID,
                AccountSymbolMapping.TradingPairID == pair.PairID
            ).first()
            
            if existing:
                if existing.AccountSymbol != detected_symbol:
                    existing.AccountSymbol = detected_symbol
                    db.commit()
                    print(f"   🔄 Updated mapping: {existing.AccountSymbol} -> {detected_symbol}")
                    mappings_updated += 1
                else:
                    print(f"   ✨ Mapping already correct: {detected_symbol}")
            else:
                mapping = AccountSymbolMapping(
                    AccountID=account.AccountID,
                    AccountSymbol=detected_symbol,
                    TradingPairID=pair.PairID
                )
                db.add(mapping)
                db.commit()
                print(f"   ✅ Created new mapping: {detected_symbol} -> {target_pair_name}")
                mappings_created += 1

        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        print(f"✅ Mappings created: {mappings_created}")
        print(f"🔄 Mappings updated: {mappings_updated}")
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
                    print(f"   ✅ {mapping.AccountSymbol} → {pair.PairNameForSearch if pair else 'Unknown'}")
            else:
                print(f"   ❌ No mappings found!")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("\n🚀 Starting Symbol Mapping Setup...")
    setup_symbol_mappings()
    verify_mappings()
    print("\n✅ All done!")
