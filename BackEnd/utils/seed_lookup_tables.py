"""
Seed script for populating lookup tables with initial data.
Run this after the database schema is created.

Usage:
    python -m utils.seed_lookup_tables
"""

from database import SessionLocal, engine
from models.asset_type import AssetType
from models.platform import Platform
from models.platform_server import PlatformServer
from models.trading_pair import TradingPair
from sqlalchemy import text


def seed_asset_types(db):
    """Seed AssetTypes table"""
    print("\n" + "="*60)
    print("Seeding AssetTypes...")
    print("="*60)
    
    asset_types = [
        {"TypeName": "Gold"},
        {"TypeName": "Cryptocurrency"},
        {"TypeName": "Forex"},
        {"TypeName": "Stocks"},
        {"TypeName": "Commodities"},
    ]
    
    for asset_data in asset_types:
        # Check if already exists
        existing = db.query(AssetType).filter(AssetType.TypeName == asset_data["TypeName"]).first()
        if not existing:
            asset = AssetType(**asset_data)
            db.add(asset)
            print(f"  ✅ Added AssetType: {asset_data['TypeName']}")
        else:
            print(f"  ⏭️  Skipped AssetType: {asset_data['TypeName']} (already exists)")
    
    db.commit()
    print("="*60)


def seed_platforms(db):
    """Seed Platforms table"""
    print("\n" + "="*60)
    print("Seeding Platforms...")
    print("="*60)
    
    platforms = [
        {"PlatformName": "MetaTrader 4"},
        {"PlatformName": "MetaTrader 5"},
        {"PlatformName": "Binance"},
        {"PlatformName": "Interactive Brokers"},
    ]
    
    for platform_data in platforms:
        # Check if already exists
        existing = db.query(Platform).filter(Platform.PlatformName == platform_data["PlatformName"]).first()
        if not existing:
            platform = Platform(**platform_data)
            db.add(platform)
            print(f"  ✅ Added Platform: {platform_data['PlatformName']}")
        else:
            print(f"  ⏭️  Skipped Platform: {platform_data['PlatformName']} (already exists)")
    
    db.commit()
    print("="*60)


def seed_platform_servers(db):
    """Seed PlatformServers table"""
    print("\n" + "="*60)
    print("Seeding PlatformServers...")
    print("="*60)
    
    # Get platform IDs
    mt4 = db.query(Platform).filter(Platform.PlatformName == "MetaTrader 4").first()
    mt5 = db.query(Platform).filter(Platform.PlatformName == "MetaTrader 5").first()
    binance = db.query(Platform).filter(Platform.PlatformName == "Binance").first()
    ib = db.query(Platform).filter(Platform.PlatformName == "Interactive Brokers").first()
    
    servers = []
    
    if mt4:
        servers.extend([
            {"PlatformID": mt4.PlatformID, "ServerName": "Real-01"},
            {"PlatformID": mt4.PlatformID, "ServerName": "Demo-Server"},
            {"PlatformID": mt4.PlatformID, "ServerName": "Live-A"},
        ])
    
    if mt5:
        servers.extend([
            {"PlatformID": mt5.PlatformID, "ServerName": "Real-01"},
            {"PlatformID": mt5.PlatformID, "ServerName": "Demo-Server"},
        ])
    
    if binance:
        servers.append({"PlatformID": binance.PlatformID, "ServerName": "Main"})
    
    if ib:
        servers.append({"PlatformID": ib.PlatformID, "ServerName": "Live"})
    
    for server_data in servers:
        # Check if already exists
        existing = db.query(PlatformServer).filter(
            PlatformServer.PlatformID == server_data["PlatformID"],
            PlatformServer.ServerName == server_data["ServerName"]
        ).first()
        
        if not existing:
            server = PlatformServer(**server_data)
            db.add(server)
            platform_name = db.query(Platform).filter(Platform.PlatformID == server_data["PlatformID"]).first().PlatformName
            print(f"  ✅ Added Server: {platform_name} - {server_data['ServerName']}")
        else:
            print(f"  ⏭️  Skipped Server (already exists)")
    
    db.commit()
    print("="*60)


def seed_trading_pairs(db):
    """Seed TradingPairs table"""
    print("\n" + "="*60)
    print("Seeding TradingPairs...")
    print("="*60)
    
    # Get asset type IDs
    gold = db.query(AssetType).filter(AssetType.TypeName == "Gold").first()
    crypto = db.query(AssetType).filter(AssetType.TypeName == "Cryptocurrency").first()
    forex = db.query(AssetType).filter(AssetType.TypeName == "Forex").first()
    
    # Get server IDs
    mt4_real = db.query(PlatformServer).join(Platform).filter(
        Platform.PlatformName == "MetaTrader 4",
        PlatformServer.ServerName == "Real-01"
    ).first()
    
    binance_main = db.query(PlatformServer).join(Platform).filter(
        Platform.PlatformName == "Binance",
        PlatformServer.ServerName == "Main"
    ).first()
    
    pairs = []
    
    if gold and mt4_real:
        pairs.append({
            "AssetTypeID": gold.AssetTypeID, 
            "ServerID": mt4_real.ServerID, 
            "OurPairName": "GOLD",
            "PairName": "XAUUSD"
        })
    
    if forex and mt4_real:
        pairs.extend([
            {"AssetTypeID": forex.AssetTypeID, "ServerID": mt4_real.ServerID, "OurPairName": "EURUSD", "PairName": "EURUSD"},
            {"AssetTypeID": forex.AssetTypeID, "ServerID": mt4_real.ServerID, "OurPairName": "GBPUSD", "PairName": "GBPUSD"},
            {"AssetTypeID": forex.AssetTypeID, "ServerID": mt4_real.ServerID, "OurPairName": "USDJPY", "PairName": "USDJPY"},
        ])
    
    if crypto and binance_main:
        pairs.extend([
            {"AssetTypeID": crypto.AssetTypeID, "ServerID": binance_main.ServerID, "OurPairName": "BTCUSDT", "PairName": "BTCUSDT"},
            {"AssetTypeID": crypto.AssetTypeID, "ServerID": binance_main.ServerID, "OurPairName": "ETHUSDT", "PairName": "ETHUSDT"},
        ])
    
    for pair_data in pairs:
        # Check if already exists
        existing = db.query(TradingPair).filter(
            TradingPair.ServerID == pair_data["ServerID"],
            TradingPair.PairName == pair_data["PairName"]
        ).first()
        
        if not existing:
            pair = TradingPair(**pair_data)
            db.add(pair)
            asset_name = db.query(AssetType).filter(AssetType.AssetTypeID == pair_data["AssetTypeID"]).first().TypeName
            print(f"  ✅ Added TradingPair: {pair_data['OurPairName']} -> {pair_data['PairName']} ({asset_name})")
        else:
            # Update OurPairName if missing
            if not existing.OurPairName:
                existing.OurPairName = pair_data["OurPairName"]
                print(f"  🔄 Updated TradingPair: {pair_data['PairName']} with OurPairName={pair_data['OurPairName']}")
            else:
                print(f"  ⏭️  Skipped TradingPair: {pair_data['PairName']} (already exists)")
    
    db.commit()
    print("="*60)


def main():
    """Main seed function"""
    print("\n" + "="*60)
    print("DATABASE SEED SCRIPT - LOOKUP TABLES")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        seed_asset_types(db)
        seed_platforms(db)
        seed_platform_servers(db)
        seed_trading_pairs(db)
        
        print("\n" + "="*60)
        print("✅ SEED COMPLETED SUCCESSFULLY")
        print("="*60)
        
        # Display summary
        print("\nSummary:")
        print(f"  AssetTypes: {db.query(AssetType).count()}")
        print(f"  Platforms: {db.query(Platform).count()}")
        print(f"  PlatformServers: {db.query(PlatformServer).count()}")
        print(f"  TradingPairs: {db.query(TradingPair).count()}")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
