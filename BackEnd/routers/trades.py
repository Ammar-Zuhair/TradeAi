from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.trade import Trade
from models.account import Account
from models.user import User
from schemas.trade import TradeCreate, TradeUpdate, TradeResponse
from utils.dependencies import get_current_user

router = APIRouter(prefix="/api/trades", tags=["Trades"])


@router.post("", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def create_trade(
    trade: TradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new trade"""
    # Verify account exists
    account = db.query(Account).filter(Account.AccountID == trade.AccountID).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Create new trade
    new_trade = Trade(
        AccountID=trade.AccountID,
        TradeTicket=trade.TradeTicket,
        TradeType=trade.TradeType,
        TradeAsset=trade.TradeAsset,
        TradeLotsize=trade.TradeLotsize,
        TradeOpenPrice=trade.TradeOpenPrice,
        TradeOpenTime=trade.TradeOpenTime,
        TradeStatus='Open'
    )
    
    db.add(new_trade)
    db.commit()
    db.refresh(new_trade)
    
    return new_trade


@router.get("", response_model=List[TradeResponse])
async def get_all_trades(
    account_id: Optional[int] = Query(None, alias="accountID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all trades, optionally filter by account ID"""
    query = db.query(Trade)
    
    if account_id is not None:
        query = query.filter(Trade.AccountID == account_id)
    
    trades = query.all()
    return trades


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trade by ID"""
    trade = db.query(Trade).filter(Trade.TradeID == trade_id).first()
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    return trade


@router.put("/{trade_id}", response_model=TradeResponse)
async def update_trade(
    trade_id: int,
    trade_update: TradeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update trade"""
    trade = db.query(Trade).filter(Trade.TradeID == trade_id).first()
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    
    # Update fields
    if trade_update.TradeClosePrice is not None:
        trade.TradeClosePrice = trade_update.TradeClosePrice
    if trade_update.TradeCloseTime is not None:
        trade.TradeCloseTime = trade_update.TradeCloseTime
    if trade_update.TradeStatus is not None:
        trade.TradeStatus = trade_update.TradeStatus
    if trade_update.TradeProfitLose is not None:
        trade.TradeProfitLose = trade_update.TradeProfitLose
    
    db.commit()
    db.refresh(trade)
    
    return trade
