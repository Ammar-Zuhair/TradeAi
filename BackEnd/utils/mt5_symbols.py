"""
Utility functions for fetching and managing MT5 symbols for user accounts.
"""

import MetaTrader5 as mt5
from typing import List, Dict, Optional
from database import SessionLocal
from models.account import Account
from models.trading_pair import TradingPair
from models.account_symbol_mapping import AccountSymbolMapping


def get_mt5_symbols(login: int, password: str, server: str) -> Optional[List[Dict[str, str]]]:
    """
    Fetch all available symbols from an MT5 account.
    
    Args:
        login: MT5 account login number
        password: MT5 account password
        server: MT5 server name
        
    Returns:
        List of dictionaries containing symbol information, or None if connection fails
        Each dict contains: {'symbol': 'XAUUSD', 'description': 'Gold vs US Dollar', 'path': 'Forex\\Metals'}
    """
    try:
        # Initialize MT5
        if not mt5.initialize():
            print(f"MT5 initialization failed: {mt5.last_error()}")
            return None
        
        # Login to account
        if not mt5.login(login=login, password=password, server=server):
            print(f"MT5 login failed: {mt5.last_error()}")
            mt5.shutdown()
            return None
        
        # Get all symbols
        symbols = mt5.symbols_get()
        
        if symbols is None:
            print("Failed to get symbols")
            mt5.shutdown()
            return None
        
        # Extract relevant information
        symbol_list = []
        for symbol in symbols:
            symbol_list.append({
                'symbol': symbol.name,
                'description': symbol.description,
                'path': symbol.path,
                'visible': symbol.visible,
                'trade_mode': symbol.trade_mode  # 0=disabled, 2=close_only, 4=full
            })
        
        # Shutdown MT5
        mt5.shutdown()
        
        return symbol_list
        
    except Exception as e:
        print(f"Error fetching MT5 symbols: {str(e)}")
        if mt5.initialize():
            mt5.shutdown()
        return None


def suggest_symbol_mapping(account_symbol: str, our_pair_names: List[str]) -> Optional[str]:
    """
    Suggest a mapping from account symbol to our standardized pair name.
    Uses fuzzy matching and common patterns.
    
    Args:
        account_symbol: Symbol from user's MT5 account (e.g., 'XAUUSD', 'GOLD.a')
        our_pair_names: List of our standardized pair names (e.g., ['GOLD', 'BTCUSDT', 'EURUSD'])
        
    Returns:
        Suggested OurPairName or None if no match found
    """
    # Common mappings
    common_mappings = {
        'XAU': 'GOLD',
        'GOLD': 'GOLD',
        'BTC': 'BTCUSDT',
        'ETH': 'ETHUSDT',
        'EUR': 'EURUSD',
        'GBP': 'GBPUSD',
        'USD': 'USDJPY',
    }
    
    # Clean the symbol (remove suffixes like .a, _pro, -m, etc.)
    clean_symbol = account_symbol.split('.')[0].split('_')[0].split('-')[0].upper()
    
    # Check common mappings first
    for key, value in common_mappings.items():
        if key in clean_symbol and value in our_pair_names:
            return value
    
    # Try exact match
    if clean_symbol in our_pair_names:
        return clean_symbol
    
    # Try partial match
    for our_name in our_pair_names:
        if our_name in clean_symbol or clean_symbol in our_name:
            return our_name
    
    return None


def create_symbol_mappings(account_id: int, mappings: List[Dict[str, int]]) -> bool:
    """
    Create symbol mappings for a user account.
    
    Args:
        account_id: Account ID
        mappings: List of dicts with {'account_symbol': 'XAUUSD', 'trading_pair_id': 1}
        
    Returns:
        True if successful, False otherwise
    """
    db = SessionLocal()
    try:
        # Delete existing mappings for this account
        db.query(AccountSymbolMapping).filter(
            AccountSymbolMapping.AccountID == account_id
        ).delete()
        
        # Create new mappings
        for mapping in mappings:
            symbol_mapping = AccountSymbolMapping(
                AccountID=account_id,
                TradingPairID=mapping['trading_pair_id'],
                AccountSymbol=mapping['account_symbol']
            )
            db.add(symbol_mapping)
        
        db.commit()
        return True
        
    except Exception as e:
        print(f"Error creating symbol mappings: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def get_trading_pair_for_symbol(account_id: int, account_symbol: str) -> Optional[int]:
    """
    Get the TradingPairID for a given account symbol.
    
    Args:
        account_id: Account ID
        account_symbol: Symbol from MT5 account
        
    Returns:
        TradingPairID or None if not found
    """
    db = SessionLocal()
    try:
        mapping = db.query(AccountSymbolMapping).filter(
            AccountSymbolMapping.AccountID == account_id,
            AccountSymbolMapping.AccountSymbol == account_symbol
        ).first()
        
        return mapping.TradingPairID if mapping else None
        
    finally:
        db.close()
