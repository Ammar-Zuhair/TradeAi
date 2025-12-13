from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class TransactionBase(BaseModel):
    TransactionType: int  # 1=Month, 2=3Months, 3=6Months, 4=Year
    TransactionAmount: Decimal
    
    @field_validator('TransactionType')
    @classmethod
    def validate_transaction_type(cls, v):
        if v not in [1, 2, 3, 4]:
            raise ValueError('TransactionType must be 1 (Month), 2 (3Months), 3 (6Months), or 4 (Year)')
        return v


class TransactionCreate(BaseModel):
    AccountID: int
    TransactionType: int  # 1=Month, 2=3Months, 3=6Months, 4=Year
    TransactionAmount: Decimal
    
    @field_validator('TransactionType')
    @classmethod
    def validate_transaction_type(cls, v):
        if v not in [1, 2, 3, 4]:
            raise ValueError('TransactionType must be 1 (Month), 2 (3Months), 3 (6Months), or 4 (Year)')
        return v


class TransactionUpdate(BaseModel):
    TransactionStatus: Optional[int] = None  # 1=Completed, 2=Pending, 3=Failed
    
    @field_validator('TransactionStatus')
    @classmethod
    def validate_transaction_status(cls, v):
        if v is not None and v not in [1, 2, 3]:
            raise ValueError('TransactionStatus must be 1 (Completed), 2 (Pending), or 3 (Failed)')
        return v


class TransactionResponse(TransactionBase):
    TransactionID: int
    AccountID: int
    TransactionDate: datetime
    TransactionEnd: Optional[datetime] = None  # ✅ Expiry
    TransactionStatus: int  # 1=Completed, 2=Pending, 3=Failed

    class Config:
        from_attributes = True

