from sqlalchemy import Column, Integer, String
from database import Base

class Platform(Base):
    __tablename__ = "Platforms"

    PlatformID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    PlatformName = Column(String(100), nullable=False, unique=True)  # e.g., 'MetaTrader 4', 'Binance'
