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
        MappingID=trade.MappingID,
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
    from models.account_symbol_mapping import AccountSymbolMapping
    from models.trading_pair import TradingPair
    from sqlalchemy.orm import joinedload
    
    query = db.query(Trade).options(
        joinedload(Trade.account_symbol_mapping).joinedload(AccountSymbolMapping.trading_pair)
    )
    
    if account_id is not None:
        query = query.filter(Trade.AccountID == account_id)
    
    trades = query.all()
    
    # Manually populate display fields
    result = []
    for trade in trades:
        t_dict = {c.name: getattr(trade, c.name) for c in trade.__table__.columns}
        
        # Add Symbol info
        if trade.account_symbol_mapping:
            t_dict['AccountSymbol'] = trade.account_symbol_mapping.AccountSymbol
            if trade.account_symbol_mapping.trading_pair:
                t_dict['PairName'] = trade.account_symbol_mapping.trading_pair.PairNameForSearch
        
        result.append(t_dict)
        
    return result


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trade by ID"""
    from models.account_symbol_mapping import AccountSymbolMapping
    from sqlalchemy.orm import joinedload
    
    trade = db.query(Trade).options(
        joinedload(Trade.account_symbol_mapping).joinedload(AccountSymbolMapping.trading_pair)
    ).filter(Trade.TradeID == trade_id).first()
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
        
    # Populate display fields
    t_dict = {c.name: getattr(trade, c.name) for c in trade.__table__.columns}
    
    if trade.account_symbol_mapping:
        t_dict['AccountSymbol'] = trade.account_symbol_mapping.AccountSymbol
        if trade.account_symbol_mapping.trading_pair:
            t_dict['PairName'] = trade.account_symbol_mapping.trading_pair.PairNameForSearch
            
    return t_dict


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


@router.post("/close/{ticket}", status_code=status.HTTP_200_OK)
async def close_single_trade(
    ticket: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Close a single trade by ticket number"""
    import MetaTrader5 as mt5
    from utils.security import decrypt
    
    # Find the trade
    trade = db.query(Trade).filter(Trade.TradeID == ticket).first()
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    
    # Get account credentials
    account = db.query(Account).filter(Account.AccountID == trade.AccountID).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
        
    # ✅ FIX: Get Server Name from ServerID relation
    from models.broker_server import BrokerServer
    server = db.query(BrokerServer).filter(BrokerServer.ServerID == account.ServerID).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker Server not found for this account"
        )
    
    try:
        # Initialize MT5
        if not mt5.initialize():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize MT5"
            )
        
        # Login to account
        authorized = mt5.login(
            login=account.AccountLoginNumber,
            password=decrypt(account.AccountLoginPassword),
            server=server.ServerName  # ✅ Use fetched server name
        )
        
        if not authorized:
            mt5.shutdown()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to login to MT5 account"
            )
        
        # Get position
        positions = mt5.positions_get(ticket=ticket)
        if not positions or len(positions) == 0:
            mt5.shutdown()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Position not found in MT5"
            )
        
        position = positions[0]
        
        # Prepare close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY,
            "position": ticket,
            "price": mt5.symbol_info_tick(position.symbol).bid if position.type == 0 else mt5.symbol_info_tick(position.symbol).ask,
            "deviation": 20,
            "magic": 0,
            "comment": "Closed from App",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send close order
        result = mt5.order_send(request)
        mt5.shutdown()
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to close trade: {result.comment}"
            )
        
        return {
            "success": True,
            "message": f"Trade {ticket} closed successfully",
            "ticket": ticket
        }
        
    except HTTPException as he:
        mt5.shutdown()
        raise he
    except Exception as e:
        mt5.shutdown()
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Error closing trade {ticket}: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close trade: {str(e)}"
        )


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
