"""
API Router for Symbol Mapping Management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.account import Account
from models.trading_pair import TradingPair
from models.account_symbol_mapping import AccountSymbolMapping
from utils.mt5_symbols import get_mt5_symbols, suggest_symbol_mapping, create_symbol_mappings
from routers.auth import get_current_user
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter(prefix="/api/symbols", tags=["Symbol Mapping"])


# ============= Schemas =============

class MT5SymbolResponse(BaseModel):
    symbol: str
    description: str
    path: str
    visible: bool
    trade_mode: int


class SymbolMappingRequest(BaseModel):
    account_symbol: str
    trading_pair_id: int


class SymbolMappingSuggestion(BaseModel):
    account_symbol: str
    suggested_our_pair_name: str
    suggested_trading_pair_id: int
    confidence: str  # 'high', 'medium', 'low'


class AccountSymbolMappingResponse(BaseModel):
    mapping_id: int
    account_symbol: str
    our_pair_name: str
    pair_name: str
    trading_pair_id: int
    
    class Config:
        from_attributes = True


# ============= Endpoints =============

@router.get("/mt5-symbols/{account_id}", response_model=List[MT5SymbolResponse])
async def get_account_mt5_symbols(
    account_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch all available symbols from user's MT5 account.
    This is used during account setup to map symbols.
    """
    # Verify account ownership
    account = db.query(Account).filter(
        Account.AccountID == account_id,
        Account.UserID == current_user.UserID
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or access denied"
        )
    
    # Get MT5 symbols
    symbols = get_mt5_symbols(
        login=account.AccountLoginNumber,
        password=account.AccountLoginPassword,
        server=account.AccountLoginServer
    )
    
    if symbols is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect to MT5 account or fetch symbols"
        )
    
    # Filter only tradeable symbols
    tradeable_symbols = [s for s in symbols if s['trade_mode'] == 4 and s['visible']]
    
    return tradeable_symbols


@router.get("/suggestions/{account_id}", response_model=List[SymbolMappingSuggestion])
async def get_symbol_mapping_suggestions(
    account_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get automatic suggestions for mapping MT5 symbols to our standardized pairs.
    """
    # Verify account ownership
    account = db.query(Account).filter(
        Account.AccountID == account_id,
        Account.UserID == current_user.UserID
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or access denied"
        )
    
    # Get MT5 symbols
    mt5_symbols = get_mt5_symbols(
        login=account.AccountLoginNumber,
        password=account.AccountLoginPassword,
        server=account.AccountLoginServer
    )
    
    if mt5_symbols is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch MT5 symbols"
        )
    
    # Get our standardized pair names
    trading_pairs = db.query(TradingPair).all()
    our_pair_names = list(set([tp.OurPairName for tp in trading_pairs if tp.OurPairName]))
    
    # Generate suggestions
    suggestions = []
    for mt5_symbol in mt5_symbols:
        if mt5_symbol['trade_mode'] != 4 or not mt5_symbol['visible']:
            continue
            
        suggested_name = suggest_symbol_mapping(mt5_symbol['symbol'], our_pair_names)
        
        if suggested_name:
            # Find the trading pair ID
            trading_pair = db.query(TradingPair).filter(
                TradingPair.OurPairName == suggested_name
            ).first()
            
            if trading_pair:
                suggestions.append({
                    'account_symbol': mt5_symbol['symbol'],
                    'suggested_our_pair_name': suggested_name,
                    'suggested_trading_pair_id': trading_pair.PairID,
                    'confidence': 'high' if mt5_symbol['symbol'].upper() == suggested_name else 'medium'
                })
    
    return suggestions


@router.post("/mappings/{account_id}")
async def create_account_symbol_mappings(
    account_id: int,
    mappings: List[SymbolMappingRequest],
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create or update symbol mappings for an account.
    This is called after user confirms/edits the suggested mappings.
    """
    # Verify account ownership
    account = db.query(Account).filter(
        Account.AccountID == account_id,
        Account.UserID == current_user.UserID
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or access denied"
        )
    
    # Validate trading pair IDs
    for mapping in mappings:
        trading_pair = db.query(TradingPair).filter(
            TradingPair.PairID == mapping.trading_pair_id
        ).first()
        
        if not trading_pair:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid trading pair ID: {mapping.trading_pair_id}"
            )
    
    # Create mappings
    mapping_dicts = [
        {
            'account_symbol': m.account_symbol,
            'trading_pair_id': m.trading_pair_id
        }
        for m in mappings
    ]
    
    success = create_symbol_mappings(account_id, mapping_dicts)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create symbol mappings"
        )
    
    return {"message": "Symbol mappings created successfully", "count": len(mappings)}


@router.get("/mappings/{account_id}", response_model=List[AccountSymbolMappingResponse])
async def get_account_symbol_mappings(
    account_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all symbol mappings for an account.
    """
    # Verify account ownership
    account = db.query(Account).filter(
        Account.AccountID == account_id,
        Account.UserID == current_user.UserID
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or access denied"
        )
    
    # Get mappings with joined data
    mappings = db.query(
        AccountSymbolMapping.MappingID,
        AccountSymbolMapping.AccountSymbol,
        TradingPair.OurPairName,
        TradingPair.PairName,
        TradingPair.PairID
    ).join(
        TradingPair, AccountSymbolMapping.TradingPairID == TradingPair.PairID
    ).filter(
        AccountSymbolMapping.AccountID == account_id
    ).all()
    
    return [
        {
            'mapping_id': m.MappingID,
            'account_symbol': m.AccountSymbol,
            'our_pair_name': m.OurPairName,
            'pair_name': m.PairName,
            'trading_pair_id': m.PairID
        }
        for m in mappings
    ]
