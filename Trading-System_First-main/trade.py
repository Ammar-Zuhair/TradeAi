from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from database import Base

class Trade(Base):
    __tablename__ = "Trades"

    TradeID = Column(Integer, primary_key=True, index=True, autoincrement=False) # TradeID IS the Ticket Number
    AccountID = Column(Integer, ForeignKey("Accounts.AccountID"), nullable=False)
    # TradeTicket removed, using TradeID instead
    TradeType = Column(Integer, nullable=False)  # 1=Buy, 2=Sell (TradeTypeEnum)
    TradeAsset = Column(String(10), nullable=True)  # DEPRECATED: Kept temporarily for data migration
    TradingPairID = Column(Integer, ForeignKey("TradingPairs.PairID", ondelete="RESTRICT"), nullable=True, index=True)  # New normalized reference
    TradeLotsize = Column(DECIMAL(10, 2), nullable=False)
    TradeOpenPrice = Column(DECIMAL(10, 5), nullable=False)
    TradeClosePrice = Column(DECIMAL(10, 5), nullable=True)
    TradeOpenTime = Column(DateTime, nullable=False)
    TradeCloseTime = Column(DateTime, nullable=True)
    TradeProfitLose = Column(DECIMAL(12, 2), nullable=True) # Changed to DECIMAL(12, 2) as per migration in main.py
    TradeStatus = Column(String(20), default='Open') # Winning/Losing/Open

    # Relationships
    account = relationship("Account", backref=backref("trades", cascade="all, delete-orphan"))
    trading_pair = relationship("TradingPair", backref="trades")
