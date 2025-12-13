from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class TradeCreate(BaseModel):
    TradeID: int  # Ticket Number
    AccountID: int
    TradeType: int  # 1=Buy, 2=Sell
    MappingID: int  # ✅ Required - Foreign key to AccountSymbolMappings
    TradeLotsize: Decimal  # ✅ Lot size
    TradeOpenPrice: Decimal
    TradeOpenTime: datetime
    TradeSL: Optional[Decimal] = None  # ✅ Stop Loss
    TradeTP: Optional[Decimal] = None  # ✅ Take Profit
    
    @field_validator('TradeType')
    @classmethod
    def validate_trade_type(cls, v):
        if v not in [1, 2]:
            raise ValueError('TradeType must be 1 (Buy) or 2 (Sell)')
        return v


class TradeUpdate(BaseModel):
    TradeClosePrice: Optional[Decimal] = None
    TradeCloseTime: Optional[datetime] = None
    TradeStatus: Optional[int] = None
    TradeProfitLose: Optional[Decimal] = None
    TradeSL: Optional[Decimal] = None  # ✅ Stop Loss
    TradeTP: Optional[Decimal] = None  # ✅ Take Profit



class TradeResponse(BaseModel):
    TradeID: int
    AccountID: int
    TradeType: int  # 1=Buy, 2=Sell
    MappingID: Optional[int] = None
    TradeLotsize: Decimal  # ✅ Lot size for display
    TradeOpenPrice: Decimal
    TradeOpenTime: datetime
    TradeSL: Optional[Decimal] = None  # ✅ Stop Loss
    TradeTP: Optional[Decimal] = None  # ✅ Take Profit
    TradeClosePrice: Optional[Decimal] = None
    TradeCloseTime: Optional[datetime] = None
    TradeStatus: int
    TradeStatus: int
    TradeProfitLose: Optional[Decimal] = None
    
    # ✅ Added for display
    AccountSymbol: Optional[str] = None  # e.g., "XAUUSD.m"
    PairName: Optional[str] = None       # e.g., "GOLD"
    
    class Config:
        from_attributes = True
