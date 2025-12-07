from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime


class UserBase(BaseModel):
    Email: EmailStr
    UserIDcardrName: str


class UserCreate(UserBase):
    Password: str
    UserIDCardrNumber: Optional[int] = None
    PhoneNumber: Optional[str] = None
    Address: Optional[str] = None
    DateOfBirth: Optional[date] = None


class UserUpdate(BaseModel):
    UserIDcardrName: Optional[str] = None
    Email: Optional[EmailStr] = None
    Password: Optional[str] = None
    UserStatus: Optional[bool] = None
    UserIDCardrNumber: Optional[int] = None
    PhoneNumber: Optional[str] = None
    Address: Optional[str] = None
    DateOfBirth: Optional[date] = None


class UserResponse(UserBase):
    UserID: int
    UserStatus: bool
    UserIDCardrNumber: Optional[int] = None
    PhoneNumber: Optional[str] = None
    Address: Optional[str] = None
    DateOfBirth: Optional[date] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True
