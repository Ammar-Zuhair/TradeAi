from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime
from enum import Enum as PyEnum

class TradingStrategyEnum(str, PyEnum):
    """Trading strategy types for automated trading"""
    ADVANCED = "All"  # FVG + Trend + Prediction + Voting
    SIMPLE = "FVG + Trend"      # FVG + Trend only
    VOTING = "Voting"      # Full Voting System (7 Models) + Price Prediction

class Account(Base):
    __tablename__ = "Accounts"

    AccountID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    UserID = Column(Integer, ForeignKey("Users.UserID"), nullable=False)
    AccountType = Column(String(10), nullable=False) # Demo / Real
    AccountBalance = Column(DECIMAL(12, 2), default=0.00)
    AccountCreationDate = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())
    AccountLoginNumber = Column(Integer, nullable=True)
    AccountLoginPassword = Column(String(255), nullable=True)
    AccountLoginServer = Column(String(100), nullable=True)
    RiskPercentage = Column(DECIMAL(4, 2), default=1.00, nullable=False)  # Max 10.00%
    TradingStrategy = Column(String(20), default='None', nullable=True)  # Trading strategy type

    # Relationship
    owner = relationship("User", backref="accounts")

