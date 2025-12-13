from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class TradingPair(Base):
    __tablename__ = "TradingPairs"

    PairID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    AssetTypeID = Column(Integer, ForeignKey("AssetTypes.AssetTypeID", ondelete="CASCADE"), nullable=False, index=True)
    PairNameForSearch = Column(String(10), nullable=False, index=True)  # Standardized name used for searching symbols (e.g., 'GOLD')
    
    # Unique constraint: prevent duplicate pairs (globally unique standard names)
    __table_args__ = (
        UniqueConstraint('PairNameForSearch', name='uq_pair_name_for_search'),
    )

    # Relationships
    asset_type = relationship("AssetType", backref="trading_pairs")
    # server relationship removed
