from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class TradeCreate(BaseModel):
    TradeID: int  # Ticket Number
    AccountID: int
    TradeType: int  # 1=Buy, 2=Sell
    TradingPairID: Optional[int] = None  # Foreign key to TradingPairs
    TradeAsset: Optional[str] = None  # DEPRECATED: Use TradingPairID instead
    TradeLotsize: Decimal
    TradeOpenPrice: Decimal
    TradeOpenTime: datetime
    
    @field_validator('TradeType')
    @classmethod
    def validate_trade_type(cls, v):
        if v not in [1, 2]:
            raise ValueError('TradeType must be 1 (Buy) or 2 (Sell)')
        return v


class TradeUpdate(BaseModel):
    TradeClosePrice: Optional[Decimal] = None
    TradeCloseTime: Optional[datetime] = None
    TradeStatus: Optional[str] = None
    TradeProfitLose: Optional[Decimal] = None


class TradeResponse(BaseModel):
    TradeID: int
    AccountID: int
    TradeType: int  # 1=Buy, 2=Sell
    TradingPairID: Optional[int] = None
    TradeAsset: Optional[str] = None  # DEPRECATED
    TradeLotsize: Decimal
    TradeOpenPrice: Decimal
    TradeOpenTime: datetime
    TradeClosePrice: Optional[Decimal] = None
    TradeCloseTime: Optional[datetime] = None
    TradeStatus: str
    TradeProfitLose: Optional[Decimal] = None
    
    class Config:
        from_attributes = True
