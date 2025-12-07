from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class TradeBase(BaseModel):
    TradeSymbol: Optional[str] = None # Renamed from TradeAsset in model? No, model has TradeAsset.
    # Let's check model again.
    # Model: TradeAsset, TradeType, TradeLotsize, TradeOpenPrice, TradeOpenTime, TradeStatus, TradeProfitLose
    # Schema used TradeSymbol. Let's align with Model or keep as is if mapped.
    # Router maps TradeSymbol -> TradeSymbol? No, Router: TradeSymbol=trade.TradeSymbol.
    # Model doesn't have TradeSymbol! Model has TradeAsset.
    # I should check routers/trades.py again.
    pass

class TradeCreate(BaseModel):
    AccountID: int
    TradeType: str
    TradeAsset: str
    TradeLotsize: Decimal
    TradeOpenPrice: Decimal
    TradeOpenTime: datetime
    TradeTicket: Optional[int] = None

class TradeUpdate(BaseModel):
    TradeClosePrice: Optional[Decimal] = None
    TradeCloseTime: Optional[datetime] = None
    TradeStatus: Optional[str] = None
    TradeProfitLose: Optional[Decimal] = None # Fixed name

class TradeResponse(BaseModel):
    TradeID: int
    AccountID: int
    TradeTicket: Optional[int] = None
    TradeType: str
    TradeAsset: str
    TradeLotsize: Decimal
    TradeOpenPrice: Decimal
    TradeOpenTime: datetime
    TradeClosePrice: Optional[Decimal] = None
    TradeCloseTime: Optional[datetime] = None
    TradeStatus: str
    TradeProfitLose: Optional[Decimal] = None # Fixed name
    
    class Config:
        from_attributes = True
