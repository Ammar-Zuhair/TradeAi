from pydantic import BaseModel, field_validator
from typing import Optional, Literal, Dict, Any
from datetime import datetime
from decimal import Decimal

# Trading strategy types
TradingStrategyType = Literal["All", "FVG + Trend", "Voting"]


class AccountBase(BaseModel):
    AccountType: Optional[str] = "Unknown"
    AccountLoginServer: Optional[str] = None
    AccountLoginNumber: Optional[int] = None
    TradingStrategy: Optional[TradingStrategyType] = "All"


class AccountCreate(AccountBase):
    UserID: int
    AccountLoginPassword: Optional[str] = None
    RiskPercentage: Optional[Decimal] = Decimal('1.00')
    TradingStrategy: Optional[TradingStrategyType] = "All"
    
    @field_validator('RiskPercentage')
    @classmethod
    def validate_risk_percentage(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError('Risk percentage cannot be negative')
            if v > 10:
                raise ValueError('Risk percentage cannot exceed 10%')
        return v


class AccountUpdate(BaseModel):
    AccountType: Optional[str] = None
    AccountLoginServer: Optional[str] = None
    AccountLoginNumber: Optional[int] = None
    AccountLoginPassword: Optional[str] = None
    AccountBalance: Optional[Decimal] = None
    RiskPercentage: Optional[Decimal] = None
    TradingStrategy: Optional[TradingStrategyType] = None
    
    @field_validator('RiskPercentage')
    @classmethod
    def validate_risk_percentage(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError('Risk percentage cannot be negative')
            if v > 10:
                raise ValueError('Risk percentage cannot exceed 10%')
        return v


class AccountResponse(AccountBase):
    AccountID: int
    UserID: int
    AccountBalance: Decimal
    RiskPercentage: Decimal
    TradingStrategy: str
    AccountCreationDate: Optional[datetime] = None

    class Config:
        from_attributes = True


class MT5VerificationResponse(BaseModel):
    """Response schema for MT5 account verification"""
    success: bool
    message: str
    account: Optional[AccountResponse] = None
    mt5_info: Optional[Dict[str, Any]] = None  # Additional MT5 account details

