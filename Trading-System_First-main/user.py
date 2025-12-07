from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, BigInteger
from sqlalchemy.sql import func
from BackEnd.database import Base
from BackEnd.utils.security import hash_password, verify_password
from datetime import datetime

class User(Base):
    __tablename__ = "Users"

    UserID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    UserIDcardrName = Column(String(50), nullable=False)
    UserIDCardrNumber = Column(BigInteger, nullable=True) # Changed to nullable as it might not be available at signup or for existing users
    Email = Column(String(30), unique=True, nullable=False, index=True)
    Password = Column(String(255), nullable=False) # Increased length for hashed password
    UserStatus = Column(Boolean, default=True)
    DateOfBirth = Column(Date, nullable=True)
    Address = Column(String(50), nullable=True)
    PhoneNumber = Column(String(15), nullable=True)
    
    # Timestamps (kept for internal tracking, though not explicitly requested, they are good practice)
    createdAt = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return verify_password(password, self.Password)

    def set_password(self, password: str):
        """Hash and set password"""
        self.Password = hash_password(password)
