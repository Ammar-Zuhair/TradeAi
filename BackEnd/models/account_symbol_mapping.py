from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class AccountSymbolMapping(Base):
    """
    Maps user account symbols to our standardized trading pairs.
    This allows different MT5/MT4 accounts to have different symbol names
    for the same underlying asset (e.g., 'XAUUSD', 'GOLD.a', 'GOLD_m' all map to 'GOLD')
    """
    __tablename__ = "AccountSymbolMappings"

    MappingID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    AccountID = Column(Integer, ForeignKey("Accounts.AccountID", ondelete="CASCADE"), nullable=False, index=True)
    PairID = Column(Integer, ForeignKey("TradingPairs.PairID", ondelete="CASCADE"), nullable=False, index=True)
    AccountSymbol = Column(String(10), nullable=False)  # The actual symbol name in the user's MT5/MT4 account
    
    # Relationships
    account = relationship("Account", backref="symbol_mappings")
    trading_pair = relationship("TradingPair", backref="account_mappings")
    
    # Note: We don't add a unique constraint here because theoretically
    # the same symbol could map to different pairs on different servers,
    # but AccountID already ensures uniqueness per account
