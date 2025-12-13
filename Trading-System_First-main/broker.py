from sqlalchemy import Column, Integer, String
from database import Base

class Broker(Base):
    __tablename__ = "Brokers"

    BrokerID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    BrokerName = Column(String(100), nullable=False, unique=True)  # e.g., 'MetaTrader 5', 'MetaTrader 4', 'Binance'
