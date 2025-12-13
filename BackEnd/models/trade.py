from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from database import Base

class Trade(Base):
    __tablename__ = "Trades"

    TradeID = Column(Integer, primary_key=True, index=True)  # MT5 Ticket Number
    AccountID = Column(Integer, ForeignKey("Accounts.AccountID", ondelete="CASCADE"), nullable=False, index=True)
    # TradeTicket removed, using TradeID instead
    TradeType = Column(Integer, nullable=False)  # 1=Buy, 2=Sell (TradeTypeEnum)
    MappingID = Column(Integer, ForeignKey("AccountSymbolMappings.MappingID", ondelete="SET NULL"), nullable=True, index=True)  # ✅ Foreign Key
    TradeLotsize = Column(DECIMAL(4, 2), nullable=False)  # ✅ Lot size for display
    TradeOpenPrice = Column(DECIMAL(10, 5), nullable=False)
    TradeOpenTime = Column(DateTime(timezone=True), nullable=False)
    TradeSL = Column(DECIMAL(12, 5), nullable=True)  # ✅ Stop Loss
    TradeTP = Column(DECIMAL(12, 5), nullable=True)  # ✅ Take Profit
    TradeClosePrice = Column(DECIMAL(10, 5), nullable=True)
    TradeCloseTime = Column(DateTime(timezone=True), nullable=True)
    TradeProfitLose = Column(DECIMAL(12, 2), nullable=True) # Changed to DECIMAL(12, 2) as per migration in main.py
    TradeStatus = Column(Integer, default=1)  # 1=Open, 2=Winning, 3=Losing

    # Relationships
    account = relationship("Account", backref=backref("trades", cascade="all, delete-orphan"))
    account_symbol_mapping = relationship("AccountSymbolMapping", backref="trades")  # ✅ Relationship to TradingPair

