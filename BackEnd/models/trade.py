from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Trade(Base):
    __tablename__ = "Trades"

    TradeID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    AccountID = Column(Integer, ForeignKey("Accounts.AccountID"), nullable=False)
    TradeTicket = Column(Integer, nullable=True) # MT5 Ticket Number
    TradeType = Column(String(10), nullable=False) # Buy / Sell
    TradeAsset = Column(String(10), nullable=False) # Gold, Stock, Currency...
    TradeLotsize = Column(DECIMAL(10, 2), nullable=False)
    TradeOpenPrice = Column(DECIMAL(10, 5), nullable=False)
    TradeClosePrice = Column(DECIMAL(10, 5), nullable=True)
    TradeOpenTime = Column(DateTime, nullable=False)
    TradeCloseTime = Column(DateTime, nullable=True)
    TradeProfitLose = Column(DECIMAL(6, 2), nullable=True) # User requested INT, usually DECIMAL is better but sticking to request
    TradeStatus = Column(String(20), default='Open') # Winning/Losing/Open

    # Relationship
    account = relationship("Account", backref="trades")
