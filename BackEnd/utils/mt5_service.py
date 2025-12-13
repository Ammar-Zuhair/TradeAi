"""
MT5 Service - MetaTrader 5 Connection and Account Verification
==============================================================

This service handles:
1. MT5 connection verification
2. Account information retrieval
3. Balance and equity fetching
"""

import MetaTrader5 as mt5
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MT5Service:
    """Service for MT5 operations"""
    
    @staticmethod
    def verify_and_get_account_info(
        login: int,
        password: str,
        server: str
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Verify MT5 account credentials and fetch account information
        
        Args:
            login: MT5 account login number
            password: MT5 account password
            server: MT5 broker server name
            
        Returns:
            Tuple of (success, account_info_dict, error_message)
        """
        try:
            # Initialize MT5 with specific account
            if not mt5.initialize(login=login, password=password, server=server):
                error = f"MT5 initialization failed: {mt5.last_error()}"
                logger.error(error)
                return False, None, error
            
            # Attempt login
            authorized = mt5.login(login=login, password=password, server=server)
            
            if not authorized:
                error_code, error_msg = mt5.last_error()
                error = f"MT5 login failed: {error_msg} (Code: {error_code})"
                logger.error(error)
                mt5.shutdown()
                return False, None, error
            
            # Get account information
            account_info = mt5.account_info()
            
            if account_info is None:
                error = "Failed to retrieve account information"
                logger.error(error)
                mt5.shutdown()
                return False, None, error
            
            # Extract relevant information
            account_data = {
                "login": account_info.login,
                "balance": float(account_info.balance),
                "equity": float(account_info.equity),
                "margin": float(account_info.margin),
                "margin_free": float(account_info.margin_free),
                "margin_level": float(account_info.margin_level) if account_info.margin > 0 else 0.0,
                "profit": float(account_info.profit),
                "leverage": account_info.leverage,
                "server": account_info.server,
                "currency": account_info.currency,
                "name": account_info.name,
                "company": account_info.company,
                "trade_mode": MT5Service._get_trade_mode_name(account_info.trade_mode)
            }
            
            # Shutdown MT5 connection
            mt5.shutdown()
            
            logger.info(f"Successfully verified MT5 account: {login}")
            return True, account_data, None
            
        except Exception as e:
            error = f"Unexpected error during MT5 verification: {str(e)}"
            logger.error(error)
            try:
                mt5.shutdown()
            except:
                pass
            return False, None, error
    
    @staticmethod
    def _get_trade_mode_name(trade_mode: int) -> str:
        """Convert trade mode code to readable name"""
        modes = {
            0: "Demo",
            1: "Contest",
            2: "Real"
        }
        return modes.get(trade_mode, "Unknown")
    
    @staticmethod
    def test_connection(login: int, password: str, server: str) -> Tuple[bool, Optional[str]]:
        """
        Quick test of MT5 connection without fetching full account info
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not mt5.initialize():
                return False, f"MT5 initialization failed: {mt5.last_error()}"
            
            authorized = mt5.login(login=login, password=password, server=server)
            mt5.shutdown()
            
            if not authorized:
                error_code, error_msg = mt5.last_error()
                return False, f"Login failed: {error_msg} (Code: {error_code})"
            
            return True, None
            
        except Exception as e:
            try:
                mt5.shutdown()
            except:
                pass
            return False, f"Connection test failed: {str(e)}"
    
    @staticmethod
    async def get_account_info(login: int, password: str, server: str) -> Optional[Dict]:
        """
        Get current account information (balance, equity, etc.)
        
        Returns:
            Dict with account info or None if failed
        """
        try:
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return None
            
            if not mt5.login(login=login, password=password, server=server):
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                mt5.shutdown()
                return None
            
            account_info = mt5.account_info()
            mt5.shutdown()
            
            if account_info is None:
                return None
            
            return {
                "balance": float(account_info.balance),
                "equity": float(account_info.equity),
                "profit": float(account_info.profit),
                "margin": float(account_info.margin),
                "margin_free": float(account_info.margin_free),
            }
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            try:
                mt5.shutdown()
            except:
                pass
            return None
    
    @staticmethod
    async def get_open_positions(login: int, password: str, server: str, symbol: str = None) -> Optional[list]:
        """
        Get all open positions for an account
        
        Args:
            symbol: Optional symbol filter (e.g., 'XAUUSD')
            
        Returns:
            List of position dicts or None if failed
        """
        try:
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return None
            
            if not mt5.login(login=login, password=password, server=server):
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                mt5.shutdown()
                return None
            
            # Get positions
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            
            mt5.shutdown()
            
            if positions is None:
                return []
            
            # Convert to list of dicts
            result = []
            for pos in positions:
                result.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': pos.type,  # 0=BUY, 1=SELL
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'profit': pos.profit,
                    'sl': pos.sl,
                    'tp': pos.tp,
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            try:
                mt5.shutdown()
            except:
                pass
            return None
    
    @staticmethod
    async def get_trade_history(login: int, password: str, server: str, ticket: int) -> Optional[Dict]:
        """
        Get trade history details for a specific ticket
        
        Returns:
            Dict with trade history or None if not found
        """
        try:
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return None
            
            if not mt5.login(login=login, password=password, server=server):
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                mt5.shutdown()
                return None
            
            # Get deals for this ticket
            from datetime import datetime, timedelta
            # Look back 30 days for the trade
            date_from = datetime.now() - timedelta(days=30)
            date_to = datetime.now()
            
            deals = mt5.history_deals_get(date_from, date_to)
            
            mt5.shutdown()
            
            if deals is None or len(deals) == 0:
                return None
            
            # Find the closing deal for this ticket
            for deal in deals:
                if deal.position_id == ticket and deal.entry == 1:  # 1 = OUT (closing deal)
                    return {
                        'ticket': deal.position_id,
                        'close_price': deal.price,
                        'close_time': datetime.fromtimestamp(deal.time),
                        'profit': deal.profit,
                        'volume': deal.volume,
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            try:
                mt5.shutdown()
            except:
                pass
            return None
