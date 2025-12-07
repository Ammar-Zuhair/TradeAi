from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime

class Transaction(Base):
    __tablename__ = "Transactions"

    TransactionID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    AccountID = Column(Integer, ForeignKey("Accounts.AccountID"), nullable=False)
    TransactionType = Column(String(50), nullable=False) # Deposit / Withdrawal / Transfer
    TransactionAmount = Column(DECIMAL(12, 2), nullable=False)
    TransactionDate = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())
    TransactionStatus = Column(String(20), default='Pending') # Completed / Pending / Failed

    # Relationship
    account = relationship("Account", backref="transactions")
