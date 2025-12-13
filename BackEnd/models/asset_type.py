from sqlalchemy import Column, Integer, String
from database import Base

class AssetType(Base):
    __tablename__ = "AssetTypes"

    AssetTypeID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    TypeName = Column(String(10), nullable=False, unique=True)  # e.g., 'Gold', 'Cryptocurrency', 'Stocks', 'Forex'
