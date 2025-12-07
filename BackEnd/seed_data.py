from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models.trade import Trade
from models.account import Account
from datetime import datetime, timedelta
from decimal import Decimal
import random

def seed_data():
    db: Session = SessionLocal()
    
    try:
        print("🌱 Starting data seeding...")
        
        # Ensure tables exist
        Base.metadata.create_all(bind=engine)
        
        # Check if accounts 1, 2, 3 exist, if not create dummy ones
        for i in range(1, 4):
            account = db.query(Account).filter(Account.AccountID == i).first()
            if not account:
                print(f"⚠️ Account {i} not found. Creating dummy account...")
                new_account = Account(
                    AccountID=i,
                    UserID=1, # Assuming User 1 exists
                    AccountType="Real",
                    AccountBalance=10000.00,
                    AccountLoginNumber=1000 + i,
                    AccountLoginPassword="password",
                    AccountLoginServer="Demo-Server",
                    RiskPercentage=1.0,
                    TradingStrategy="All"
                )
                db.add(new_account)
                db.commit()
                print(f"✅ Created Account {i}")

        # Define Trades Data
        # Format: (TradeID/Ticket, AccountID, Type, Asset, Lotsize, OpenPrice, ClosePrice, OpenTime, CloseTime, Profit, Status)
        trades_data = [
            # Account 1: Mixed
            (1001, 1, "BUY", "XAUUSD", 0.10, 2000.50, None, datetime.now() - timedelta(hours=2), None, None, "Open"),
            (1002, 1, "SELL", "EURUSD", 0.50, 1.0850, 1.0820, datetime.now() - timedelta(days=1), datetime.now() - timedelta(days=1, hours=4), 150.00, "Winning"),
            (1003, 1, "BUY", "GBPUSD", 0.20, 1.2500, 1.2480, datetime.now() - timedelta(days=2), datetime.now() - timedelta(days=2, hours=5), -40.00, "Losing"),
            
            # Account 2: Mostly Open/Losing
            (2001, 2, "SELL", "US30", 0.10, 34000.00, None, datetime.now() - timedelta(minutes=30), None, -15.00, "Open"), # Open but currently losing (floating PL)
            (2002, 2, "BUY", "NAS100", 0.10, 15000.00, 14950.00, datetime.now() - timedelta(days=1), datetime.now() - timedelta(days=1, hours=2), -100.00, "Losing"),
            
            # Account 3: Mostly Winning
            (3001, 3, "BUY", "BTCUSD", 0.05, 45000.00, 46000.00, datetime.now() - timedelta(days=3), datetime.now() - timedelta(days=2), 500.00, "Winning"),
            (3002, 3, "SELL", "ETHUSD", 0.50, 2500.00, 2400.00, datetime.now() - timedelta(hours=5), datetime.now() - timedelta(hours=1), 500.00, "Winning"),
            (3003, 3, "BUY", "XAUUSD", 0.10, 2010.00, None, datetime.now() - timedelta(minutes=10), None, 5.00, "Open"), # Open and winning
        ]

        for data in trades_data:
            tid, acc_id, t_type, asset, lot, open_p, close_p, open_t, close_t, profit, status = data
            
            # Check if trade exists
            existing = db.query(Trade).filter(Trade.TradeID == tid).first()
            if existing:
                print(f"ℹ️ Trade {tid} already exists. Skipping.")
                continue
                
            trade = Trade(
                TradeID=tid,
                AccountID=acc_id,
                TradeType=t_type,
                TradeAsset=asset,
                TradeLotsize=Decimal(str(lot)),
                TradeOpenPrice=Decimal(str(open_p)),
                TradeClosePrice=Decimal(str(close_p)) if close_p else None,
                TradeOpenTime=open_t,
                TradeCloseTime=close_t,
                TradeProfitLose=Decimal(str(profit)) if profit is not None else None,
                TradeStatus=status
            )
            db.add(trade)
            print(f"✅ Added Trade {tid} for Account {acc_id} ({status})")
            
        db.commit()
        print("🎉 Seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
