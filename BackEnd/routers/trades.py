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
        TradeID=trade.TradeID, # Use provided ID (Ticket)
        AccountID=trade.AccountID,
        # TradeTicket removed
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
    
    # Send Notification
    try:
        if current_user.IsNotificationsEnabled and current_user.PushToken:
            from utils.notifications import send_push_notification
            send_push_notification(
                token=current_user.PushToken,
                title="New Trade Opened 🚀",
                body=f"{trade.TradeType} {trade.TradeAsset} @ {trade.TradeOpenPrice}",
                data={"trade_id": new_trade.TradeID}
            )
    except Exception as e:
        print(f"⚠️ Failed to send notification: {e}")
    
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


@router.post("/close-all/{account_id}", status_code=status.HTTP_200_OK)
async def close_all_trades(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Close all open trades for a specific account"""
    # Verify account exists
    account = db.query(Account).filter(Account.AccountID == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Find all open trades
    open_trades = db.query(Trade).filter(
        Trade.AccountID == account_id,
        Trade.TradeStatus == 'Open'
    ).all()
    
    if not open_trades:
        return {"message": "No open trades to close", "count": 0}
    
    from datetime import datetime
    
    count = 0
    for trade in open_trades:
        trade.TradeStatus = 'Closed'
        trade.TradeCloseTime = datetime.now()
        # In a real scenario, we would need the close price and calculate profit
        # For now, we'll just mark them as closed. 
        # Optionally set close price = open price (break even) if unknown
        if not trade.TradeClosePrice:
            trade.TradeClosePrice = trade.TradeOpenPrice
        if not trade.TradeProfitLose:
            trade.TradeProfitLose = 0.0
            
        count += 1
        
    db.commit()
    
    return {"message": f"Successfully closed {count} trades", "count": count}
