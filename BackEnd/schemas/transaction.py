from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class TransactionBase(BaseModel):
    Type: str  # Deposit, Withdrawal
    Amount: Decimal


class TransactionCreate(TransactionBase):
    AccountID: int


class TransactionResponse(TransactionBase):
    TransactionID: int
    AccountID: int
    Date: datetime
    Status: str
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True
