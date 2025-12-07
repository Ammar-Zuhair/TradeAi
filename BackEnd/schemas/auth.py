from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    otp: str
    # Optional fields for registration
    idCardNumber: Optional[str] = None
    phoneNumber: Optional[str] = None
    address: Optional[str] = None
    dateOfBirth: Optional[date] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class OTPRequest(BaseModel):
    email: EmailStr
    name: str


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    email: EmailStr
    otp: str
    newPassword: str


class GoogleAuthRequest(BaseModel):
    idToken: str


class FacebookAuthRequest(BaseModel):
    accessToken: str
