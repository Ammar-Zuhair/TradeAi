from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from database import Base

class Trade(Base):
    __tablename__ = "Trades"

    TradeID = Column(Integer, primary_key=True, index=True, autoincrement=False) # TradeID IS the Ticket Number
    AccountID = Column(Integer, ForeignKey("Accounts.AccountID"), nullable=False)
    # TradeTicket removed, using TradeID instead
    TradeType = Column(String(10), nullable=False) # Buy / Sell
    TradeAsset = Column(String(10), nullable=False) # Gold, Stock, Currency...
    TradeLotsize = Column(DECIMAL(10, 2), nullable=False)
    TradeOpenPrice = Column(DECIMAL(10, 5), nullable=False)
    TradeClosePrice = Column(DECIMAL(10, 5), nullable=True)
    TradeOpenTime = Column(DateTime, nullable=False)
    TradeCloseTime = Column(DateTime, nullable=True)
    TradeProfitLose = Column(DECIMAL(12, 2), nullable=True) # Changed to DECIMAL(12, 2) as per migration in main.py
    TradeStatus = Column(String(20), default='Open') # Winning/Losing/Open

    # Relationship
    # Relationship
    account = relationship("Account", backref=backref("trades", cascade="all, delete-orphan"))
