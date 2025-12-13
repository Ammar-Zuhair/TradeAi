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
        # Initialize MT5 with specific account
        if not mt5.initialize(login=login, password=password, server=server):
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


def find_best_match_for_asset(account_symbols: List[str], target_asset: str) -> Optional[str]:
    """
    Find the best matching symbol from account_symbols for a given target asset (e.g. 'GOLD', 'XAUUSD').
    """
    target = target_asset.upper()
    
    # 1. Exact variations priority list
    variations = [
        target,
        "GOLD" if target == "XAUUSD" else target,
        "XAUUSD" if target == "GOLD" else target,
        f"{target}m", f"{target}.m", 
        f"{target}pro", f"{target}_pro",
        f"{target}ecn", f"{target}.a",
        f"{target}+"
    ]
    
    # Check exact variations first
    for var in variations:
        if var in account_symbols:
            return var
            
    # 2. Fuzzy/Keyword Search
    # If target is Gold-related
    if target in ['GOLD', 'XAUUSD']:
        keywords = ['XAU', 'GOLD']
        for sym in account_symbols:
            for kw in keywords:
                if kw in sym:
                    return sym
    
    return None

def suggest_symbol_mapping(account_id: int, available_symbols: List[Dict[str, str]]) -> List[Dict[str, any]]:
    """
    Suggest mappings for standard trading pairs based on available account symbols.
    
    Args:
        account_id: Account ID
        available_symbols: List of dicts from get_mt5_symbols
        
    Returns:
        List of dicts: [{'account_symbol': 'XAUUSD.m', 'suggested_trading_pair_id': 1}]
    """
    db = SessionLocal()
    suggestions = []
    
    try:
        # Get all our standardized trading pairs
        trading_pairs = db.query(TradingPair).all()
        
        # Extract just the symbol names for searching
        account_symbol_names = [s['symbol'] for s in available_symbols]
        
        for pair in trading_pairs:
            print(f"DEBUG: Searching for pair {pair.PairNameForSearch}...", flush=True)
            # Try to find a match for this pair (e.g. XAUUSDm / XAUUSD)
            # Use PairNameForSearch (standard name like GOLD) as the search target
            match = find_best_match_for_asset(account_symbol_names, pair.PairNameForSearch)
            
            if match:
                print(f"DEBUG: FOUND MATCH: {pair.PairNameForSearch} -> {match}", flush=True)
                suggestions.append({
                    'account_symbol': match,
                    'suggested_trading_pair_id': pair.PairID,
                    'pair_name': pair.PairNameForSearch
                })
            else:
                print(f"DEBUG: NO MATCH FOUND for {pair.PairNameForSearch}", flush=True)
                
        return suggestions
        
    finally:
        db.close()


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
                PairID=mapping['trading_pair_id'],
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
        
        return mapping.PairID if mapping else None
        
    finally:
        db.close()


def update_mappings_for_new_pair(pair_id: int, pair_name: str) -> Dict[str, int]:
    """
    When a new TradingPair is added by Admin, this function iterates through
    ALL active accounts and tries to find/create a mapping for this new pair.
    
    Returns:
        Dict with stats: {'success': 5, 'failed': 2, 'skipped': 10}
    """
    db = SessionLocal()
    stats = {'success': 0, 'failed': 0, 'skipped': 0}
    
    try:
        # 1. Get all active accounts (Real and Demo) that are connected
        # defined as having a LoginNumber and Password and ServerID
        accounts = db.query(Account).filter(
            Account.AccountLoginNumber.isnot(None),
            Account.AccountLoginPassword.isnot(None),
            Account.ServerID.isnot(None)
        ).all()
        
        print(f"🔄 Auto-Mapping: Found {len(accounts)} accounts to check for new pair '{pair_name}'")
        
        for account in accounts:
            try:
                # Get server name
                from models.broker_server import BrokerServer
                server = db.query(BrokerServer).filter(BrokerServer.ServerID == account.ServerID).first()
                if not server:
                    stats['skipped'] += 1
                    continue
                    
                server_name = server.ServerName
                
                # Check if mapping already exists (unlikely for new pair, but good practice)
                exists = db.query(AccountSymbolMapping).filter(
                    AccountSymbolMapping.AccountID == account.AccountID,
                    AccountSymbolMapping.PairID == pair_id
                ).first()
                
                if exists:
                    stats['skipped'] += 1
                    continue
                
                # Connect to MT5 and find match
                # Use cached symbols approach? No, we need to check fresh valid syms or minimal check
                # For now, simplistic approach: fetch all symbols. 
                # Optimization: In future, get_mt5_symbols could cache results or we act blindly if we knew the pattern.
                # But to be safe, we must fetch.
                
                available_symbols = get_mt5_symbols(
                    login=account.AccountLoginNumber,
                    password=account.AccountLoginPassword,
                    server=server_name
                )
                
                if not available_symbols:
                    print(f"⚠️ Failed to fetch symbols for Account {account.AccountID}")
                    stats['failed'] += 1
                    continue
                
                # Extract symbol names
                account_symbol_names = [s['symbol'] for s in available_symbols]
                
                # Find match
                match = find_best_match_for_asset(account_symbol_names, pair_name)
                
                if match:
                    # Create mapping
                    new_mapping = AccountSymbolMapping(
                        AccountID=account.AccountID,
                        PairID=pair_id,
                        AccountSymbol=match
                    )
                    db.add(new_mapping)
                    stats['success'] += 1
                    print(f"✅ Mapped '{pair_name}' -> '{match}' for Account {account.AccountID}")
                else:
                    # print(f"ℹ️ No match found for '{pair_name}' in Account {account.AccountID}")
                    pass
                    
            except Exception as e:
                print(f"❌ Error processing account {account.AccountID}: {e}")
                stats['failed'] += 1
        
        db.commit()
        return stats
        
    except Exception as e:
        print(f"❌ Critical error in auto-mapping: {e}")
        db.rollback()
        return stats
    finally:
        db.close()
