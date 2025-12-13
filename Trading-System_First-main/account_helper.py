"""
Helper functions for trading system to fetch account data and manage trades.
Used by Trading-System_First-main to interact with the database.
"""

from database import SessionLocal
from models.account import Account
from models.broker_server import BrokerServer
from models.broker import Broker
from models.account_symbol_mapping import AccountSymbolMapping
from models.trading_pair import TradingPair
from models.trade import Trade
from models.enums import AccountTypeEnum, TradeTypeEnum
from typing import Dict, Optional, List
from datetime import datetime
from decimal import Decimal



def get_account_trading_info(account_id: int) -> Optional[Dict]:
    """
    Get all necessary trading information for an account.
    Used by trading system to open trades.
    
    Args:
        account_id: Account ID from database
        
    Returns:
        Dictionary with account info:
        {
            'account_id': 1,
            'login': 12345,
            'password': 'password123',
            'server': 'Real-01',
            'platform': 'MetaTrader 4',
            'account_type': 2,  # 1=Demo, 2=Real
            'balance': 10000.00,
            'risk_percentage': 1.00,
            'symbol_mappings': {
                'GOLD': 'XAUUSD',      # OurPairName -> AccountSymbol
                'EURUSD': 'EURUSD'
            }
        }
    """
    db = SessionLocal()
    try:
        # Get account with server info
        account = db.query(Account).filter(Account.AccountID == account_id).first()
        
        if not account:
            print(f"❌ Account {account_id} not found")
            return None
        
        # ✅ Get server name from ServerID (required)
        server_name = None
        platform_name = None
        
        if account.ServerID:
            server = db.query(
                BrokerServer.ServerName,
                Broker.BrokerName
            ).join(
                Broker, BrokerServer.BrokerID == Broker.BrokerID
            ).filter(
                BrokerServer.ServerID == account.ServerID
            ).first()
            
            if server:
                server_name = server.ServerName
                broker_name = server.BrokerName
            else:
                print(f"⚠️  Server with ID {account.ServerID} not found")
                return None
        else:
            print(f"⚠️  Account {account_id} has no ServerID")
            return None
        
        # Get symbol mappings
        mappings = db.query(
            TradingPair.PairNameForSearch,
            AccountSymbolMapping.AccountSymbol
        ).join(
            TradingPair, AccountSymbolMapping.TradingPairID == TradingPair.PairID
        ).filter(
            AccountSymbolMapping.AccountID == account_id
        ).all()
        
        symbol_mappings = {
            mapping.PairNameForSearch: mapping.AccountSymbol
            for mapping in mappings
        }
        
        return {
            'account_id': account.AccountID,
            'login': account.AccountLoginNumber,
            'password': account.AccountLoginPassword,
            'server': server_name,
            'broker': broker_name,
            'account_type': account.AccountType,
            'balance': float(account.AccountBalance),
            'risk_percentage': float(account.RiskPercentage),
            'symbol_mappings': symbol_mappings
        }
        
    except Exception as e:
        print(f"❌ Error getting account info: {e}")
        return None
    finally:
        db.close()


def get_account_symbol(account_id: int, our_pair_name: str) -> Optional[str]:
    """
    Get the actual MT5 symbol for a given OurPairName.
    
    Args:
        account_id: Account ID
        our_pair_name: Our standardized pair name (e.g., 'GOLD', 'EURUSD')
        
    Returns:
        Account's actual symbol (e.g., 'XAUUSD', 'EURUSD_pro') or None
    """
    db = SessionLocal()
    try:
        mapping = db.query(AccountSymbolMapping.AccountSymbol).join(
            TradingPair, AccountSymbolMapping.TradingPairID == TradingPair.PairID
        ).filter(
            AccountSymbolMapping.AccountID == account_id,
            TradingPair.PairNameForSearch == our_pair_name
        ).first()
        
        if mapping:
            return mapping.AccountSymbol
        else:
            print(f"⚠️  No symbol mapping found for {our_pair_name} on account {account_id}")
            return None
        
    except Exception as e:
        print(f"❌ Error getting symbol: {e}")
        return None
    finally:
        db.close()


def get_trading_pair_id(account_id: int, our_pair_name: str) -> Optional[int]:
    """
    Get TradingPairID for a given OurPairName and account.
    
    Args:
        account_id: Account ID
        our_pair_name: Our standardized pair name
        
    Returns:
        TradingPairID or None
    """
    db = SessionLocal()
    try:
        mapping = db.query(AccountSymbolMapping.TradingPairID).join(
            TradingPair, AccountSymbolMapping.TradingPairID == TradingPair.PairID
        ).filter(
            AccountSymbolMapping.AccountID == account_id,
            TradingPair.PairNameForSearch == our_pair_name
        ).first()
        
        return mapping.TradingPairID if mapping else None
        
    finally:
        db.close()


def save_trade_to_db(
    trade_id: int,
    account_id: int,
    trade_type: int,  # 1=Buy, 2=Sell
    our_pair_name: str,
    lot_size: float,
    open_price: float,
    open_time: datetime,
    sl: float = None,  # ✅ Stop Loss
    tp: float = None   # ✅ Take Profit
) -> bool:
    """
    Save a new trade to the database.
    
    Args:
        trade_id: MT5 ticket number
        account_id: Account ID
        trade_type: 1=Buy, 2=Sell
        our_pair_name: Our standardized pair name (e.g., 'GOLD')
        lot_size: Trade lot size
        open_price: Opening price
        open_time: Opening time
        
    Returns:
        True if successful, False otherwise
    """
    db = SessionLocal()
    try:
        # Get TradingPairID
        trading_pair_id = get_trading_pair_id(account_id, our_pair_name)
        
        if not trading_pair_id:
            print(f"❌ Cannot save trade: No TradingPairID found for {our_pair_name}")
            return False
        
        # Create trade record
        trade = Trade(
            TradeID=trade_id,
            AccountID=account_id,
            TradeType=trade_type,
            TradingPairID=trading_pair_id,
            TradeLotsize=Decimal(str(lot_size)),
            TradeOpenPrice=Decimal(str(open_price)),
            TradeOpenTime=open_time,
            TradeSL=Decimal(str(sl)) if sl else None,  # ✅ Stop Loss
            TradeTP=Decimal(str(tp)) if tp else None,  # ✅ Take Profit
            TradeStatus=1  # Open
        )
        
        db.add(trade)
        db.commit()
        
        print(f"✅ Trade {trade_id} saved to database")
        return True
        
    except Exception as e:
        print(f"❌ Error saving trade: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def update_trade_close(
    trade_id: int,
    close_price: float,
    close_time: datetime,
    profit_loss: float
) -> bool:
    """
    Update trade with closing information.
    
    Args:
        trade_id: MT5 ticket number
        close_price: Closing price
        close_time: Closing time
        profit_loss: Profit or loss amount
        
    Returns:
        True if successful, False otherwise
    """
    db = SessionLocal()
    try:
        trade = db.query(Trade).filter(Trade.TradeID == trade_id).first()
        
        if not trade:
            print(f"❌ Trade {trade_id} not found")
            return False
        
        trade.TradeClosePrice = Decimal(str(close_price))
        trade.TradeCloseTime = close_time
        trade.TradeProfitLose = Decimal(str(profit_loss))
        
        # Update status based on profit/loss
        if profit_loss > 0:
            trade.TradeStatus = 2  # Winning
        elif profit_loss < 0:
            trade.TradeStatus = 3  # Losing
        else:
            trade.TradeStatus = 3  # Closed/Neutral
        
        db.commit()
        
        print(f"✅ Trade {trade_id} updated: P/L = {profit_loss}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating trade: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def get_active_accounts() -> List[Dict]:
    """
    Get all active trading accounts with their information.
    
    Returns:
        List of account dictionaries
    """
    db = SessionLocal()
    try:
        accounts = db.query(Account).filter(
            Account.AccountLoginNumber.isnot(None),
            Account.AccountLoginPassword.isnot(None)
        ).all()
        
        result = []
        for account in accounts:
            info = get_account_trading_info(account.AccountID)
            if info:
                result.append(info)
        
        return result
        
    finally:
        db.close()
