from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class MarketAnalysisConfig(Base):
    __tablename__ = "MarketAnalysisConfigs"

    ConfigID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    OurPairName = Column(String(10), nullable=False, index=True)  # e.g., 'GOLD', 'EURUSD'
    AccountID = Column(Integer, ForeignKey("Accounts.AccountID", ondelete="SET NULL"), nullable=True)
    IsActive = Column(Boolean, default=True)
    Timeframe = Column(String(5), default="M15")  # e.g., 'M15', 'H1'

    # Relationships
    account = relationship("Account")
