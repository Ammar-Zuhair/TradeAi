from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class PlatformServer(Base):
    __tablename__ = "PlatformServers"

    ServerID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    PlatformID = Column(Integer, ForeignKey("Platforms.PlatformID", ondelete="CASCADE"), nullable=False, index=True)
    ServerName = Column(String(100), nullable=False)  # e.g., 'Real-01', 'Demo-Server', 'Live-A'

    # Relationship
    platform = relationship("Platform", backref="servers")
