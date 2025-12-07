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
            # Initialize MT5
            if not mt5.initialize():
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
