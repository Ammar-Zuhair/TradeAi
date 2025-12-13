from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class BrokerServer(Base):
    __tablename__ = "BrokerServers"

    ServerID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    BrokerID = Column(Integer, ForeignKey("Brokers.BrokerID", ondelete="CASCADE"), nullable=False, index=True)
    ServerName = Column(String(100), nullable=False)  # e.g., 'Real-01', 'Demo-Server', 'Live-A'

    # Relationship
    broker = relationship("Broker", backref="servers")
