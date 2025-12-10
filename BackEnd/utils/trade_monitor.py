"""
Trade Monitor Service - Monitors trades and updates account balance automatically
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models.trade import Trade
from models.account import Account
from security import decrypt
from utils.mt5_service import MT5Service

logger = logging.getLogger(__name__)


class TradeMonitor:
    """Monitors trades and updates account balance when trades close"""
    
    def __init__(self):
        self.logger = logging.getLogger('TradeMonitor')
        self.mt5_service = MT5Service()
    
    async def check_and_update_closed_trades(self):
        """
        Check for recently closed trades and update account balances
        This should be called periodically (e.g., every 30 seconds)
        """
        db: Session = SessionLocal()
        try:
            # Get all open trades
            open_trades = db.query(Trade).filter(Trade.TradeStatus == 'Open').all()
            
            if not open_trades:
                return
            
            self.logger.info(f"Checking {len(open_trades)} open trades...")
            
            # Group trades by account for efficient processing
            trades_by_account = {}
            for trade in open_trades:
                account_id = trade.AccountID
                if account_id not in trades_by_account:
                    trades_by_account[account_id] = []
                trades_by_account[account_id].append(trade)
            
            # Process each account
            for account_id, trades in trades_by_account.items():
                await self._check_account_trades(db, account_id, trades)
            
            db.commit()
            
        except Exception as e:
            self.logger.error(f"Error checking trades: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def _check_account_trades(self, db: Session, account_id: int, trades: list):
        """Check trades for a specific account"""
        try:
            # Get account details
            account = db.query(Account).filter(Account.AccountID == account_id).first()
            if not account:
                self.logger.warning(f"Account {account_id} not found")
                return
            
            # Decrypt credentials
            login = account.AccountLoginNumber
            password = decrypt(account.AccountPassword)
            server = account.AccountServer
            
            # Connect to MT5 and get account info
            account_info = await self.mt5_service.get_account_info(login, password, server)
            
            if not account_info:
                self.logger.warning(f"Could not connect to MT5 for account {login}")
                return
            
            # Get current positions from MT5
            positions = await self.mt5_service.get_open_positions(login, password, server, account.AccountAsset)
            
            # Create a set of open position tickets for quick lookup
            open_tickets = set()
            if positions:
                open_tickets = {pos.get('ticket') for pos in positions if pos.get('ticket')}
            
            # Check each trade in database
            for trade in trades:
                trade_ticket = trade.TradeID  # TradeID is the MT5 ticket
                
                # If trade ticket is not in open positions, it's closed
                if trade_ticket not in open_tickets:
                    self.logger.info(f"Trade {trade_ticket} has been closed in MT5")
                    
                    # Get trade history to find close details
                    history = await self.mt5_service.get_trade_history(
                        login, password, server, 
                        trade_ticket
                    )
                    
                    if history:
                        # Update trade in database
                        trade.TradeStatus = 'Closed'
                        trade.TradeCloseTime = datetime.now()
                        trade.TradeClosePrice = history.get('close_price', trade.TradeOpenPrice)
                        trade.TradeProfitLose = history.get('profit', 0.0)
                        
                        self.logger.info(f"Updated trade {trade_ticket}: Profit/Loss = {trade.TradeProfitLose}")
            
            # Update account balance from MT5
            new_balance = account_info.get('balance', account.AccountBalance)
            if new_balance != account.AccountBalance:
                old_balance = account.AccountBalance
                account.AccountBalance = new_balance
                self.logger.info(f"Updated account {login} balance: ${old_balance:.2f} -> ${new_balance:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error checking account {account_id} trades: {e}")


# Global instance
trade_monitor = TradeMonitor()
