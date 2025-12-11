from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class TradingPair(Base):
    __tablename__ = "TradingPairs"

    PairID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    AssetTypeID = Column(Integer, ForeignKey("AssetTypes.AssetTypeID", ondelete="CASCADE"), nullable=False, index=True)
    ServerID = Column(Integer, ForeignKey("PlatformServers.ServerID", ondelete="CASCADE"), nullable=False, index=True)
    OurPairName = Column(String(50), nullable=False, index=True)  # Standardized name used in our app for analysis (e.g., 'GOLD', 'BTCUSDT', 'EURUSD')
    PairName = Column(String(50), nullable=False)  # Actual symbol in user's account (e.g., 'XAUUSD', 'GOLD.a', 'EURUSD_pro')

    # Unique constraint: prevent duplicate pairs per server
    __table_args__ = (
        UniqueConstraint('ServerID', 'PairName', name='uq_server_pair'),
    )

    # Relationships
    asset_type = relationship("AssetType", backref="trading_pairs")
    server = relationship("PlatformServer", backref="trading_pairs")

