from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime

class Transaction(Base):
    __tablename__ = "Transactions"

    TransactionID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    AccountID = Column(Integer, ForeignKey("Accounts.AccountID"), nullable=False)
    TransactionType = Column(Integer, nullable=False)  # 1=Month, 2=3Months, 3=6Months, 4=Year (TransactionTypeEnum)
    TransactionAmount = Column(DECIMAL(12, 2), nullable=False)
    TransactionDate = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())
    TransactionStatus = Column(Integer, default=2)  # 1=Completed, 2=Pending, 3=Failed (TransactionStatusEnum)

    # Relationship
    account = relationship("Account", backref="transactions")

