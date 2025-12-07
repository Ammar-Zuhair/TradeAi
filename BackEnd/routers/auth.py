from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.auth import (
    LoginRequest, RegisterRequest, TokenResponse,
    OTPRequest, OTPVerify, PasswordResetRequest, PasswordReset,
    GoogleAuthRequest, FacebookAuthRequest
)
from schemas.user import UserResponse, UserUpdate
from utils.security import (
    hash_password, verify_password, create_access_token,
    generate_otp, store_otp, verify_otp as verify_otp_code, clear_otp
)
from utils.dependencies import get_current_user
from google.auth.transport import requests
from google.oauth2 import id_token
import httpx
import os
from datetime import date

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/send-otp")
async def send_otp(request: OTPRequest, db: Session = Depends(get_db)):
    """Send OTP to email for registration"""
    # Check if email already exists
    existing_user = db.query(User).filter(User.Email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate and store OTP
    otp = generate_otp()
    store_otp(request.email, otp)
    
    # TODO: Send OTP via email service
    # For now, return it in response (ONLY FOR DEVELOPMENT)
    print(f"OTP for {request.email}: {otp}")
    
    return {
        "message": "OTP sent successfully",
        "otp": otp,  # Remove this in production
        "email": request.email
    }


@router.post("/verify-otp")
async def verify_otp_endpoint(request: OTPVerify):
    """Verify OTP code"""
    result = verify_otp_code(request.email, request.otp)
    
    if not result['valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result['message']
        )
    
    return {"message": result['message'], "verified": True}


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register new user"""
    # Verify OTP
    otp_result = verify_otp_code(request.email, request.otp)
    if not otp_result['valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=otp_result['message']
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.Email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check age
    if request.dateOfBirth:
        today = date.today()
        # Calculate age
        age = today.year - request.dateOfBirth.year - ((today.month, today.day) < (request.dateOfBirth.month, request.dateOfBirth.day))
        if age < 18:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must be at least 18 years old to register."
            )
    
    # Create new user
    new_user = User(
        UserIDcardrName=request.name,
        Email=request.email,
        Password=hash_password(request.password),
        UserStatus=True, # Active by default
        UserIDCardrNumber=int(request.idCardNumber) if request.idCardNumber else None,
        PhoneNumber=request.phoneNumber,
        Address=request.address,
        DateOfBirth=request.dateOfBirth
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate token
    access_token = create_access_token(data={"user_id": new_user.UserID})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "UserID": new_user.UserID,
            "UserName": new_user.UserIDcardrName, # Mapping for frontend compatibility if needed
            "UserEmail": new_user.Email,
            "UserStatus": new_user.UserStatus,
            "PhoneNumber": new_user.PhoneNumber,
            "Address": new_user.Address,
            "DateOfBirth": new_user.DateOfBirth,
            "UserIDCardrNumber": new_user.UserIDCardrNumber
        }
    }


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password"""
    print(f"\n{'='*50}")
    print(f"🔐 LOGIN REQUEST RECEIVED")
    print(f"{'='*50}")
    print(f"📧 Email: {request.email}")
    print(f"🔍 Searching for user in database...")
    
    try:
        # Find user
        user = db.query(User).filter(User.Email == request.email).first()
        
        if not user:
            print(f"❌ User not found: {request.email}")
            print(f"{'='*50}\n")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        print(f"✅ User found: {user.UserIDcardrName} (ID: {user.UserID})")
        print(f"🔑 Verifying password...")
        
        # Verify password
        if not verify_password(request.password, user.Password):
            print(f"❌ Password verification failed")
            print(f"{'='*50}\n")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        print(f"✅ Password verified successfully")
        print(f"📊 User Status: {user.UserStatus}")
        
        # Check user status
        if not user.UserStatus:
            print(f"❌ Account is not active: {user.UserStatus}")
            print(f"{'='*50}\n")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )
        
        print(f"🎫 Generating JWT token...")
        
        # Generate token
        access_token = create_access_token(data={"user_id": user.UserID})
        
        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "UserID": user.UserID,
                "UserName": user.UserIDcardrName,
                "UserEmail": user.Email,
                "UserStatus": user.UserStatus,
                "PhoneNumber": user.PhoneNumber,
                "Address": user.Address,
                "DateOfBirth": user.DateOfBirth,
                "UserIDCardrNumber": user.UserIDCardrNumber
            }
        }
        
        print(f"✅ Login successful!")
        print(f"👤 User: {user.UserIDcardrName}")
        print(f"📧 Email: {user.Email}")
        print(f"🆔 UserID: {user.UserID}")
        print(f"🎫 Token generated (length: {len(access_token)} chars)")
        print(f"{'='*50}\n")
        
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ INTERNAL SERVER ERROR DURING LOGIN")
        print(f"⚠️ Error: {str(e)}")
        print(f"📜 Traceback:")
        traceback.print_exc()
        print(f"{'='*50}\n")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(e)}"
        )


@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset OTP"""
    # Check if user exists
    user = db.query(User).filter(User.Email == request.email).first()
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, an OTP has been sent"}
    
    # Generate and store OTP
    otp = generate_otp()
    store_otp(request.email, otp)
    
    # TODO: Send OTP via email service
    print(f"Password Reset OTP for {request.email}: {otp}")
    
    return {
        "message": "OTP sent successfully",
        "otp": otp  # Remove this in production
    }


@router.post("/reset-password")
async def reset_password(request: PasswordReset, db: Session = Depends(get_db)):
    """Reset password with OTP"""
    # Verify OTP
    otp_result = verify_otp_code(request.email, request.otp)
    if not otp_result['valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=otp_result['message']
        )
    
    # Find user
    user = db.query(User).filter(User.Email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.Password = hash_password(request.newPassword)
    db.commit()
    
    return {"message": "Password reset successfully"}


@router.post("/google", response_model=TokenResponse)
async def google_login(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Login with Google OAuth"""
    try:
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            request.idToken,
            requests.Request(),
            os.getenv("GOOGLE_CLIENT_ID")
        )
        
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])
        
        # Check if user exists
        user = db.query(User).filter(User.Email == email).first()
        
        if not user:
            # Create new user
            user = User(
                UserIDcardrName=name,
                Email=email,
                Password=hash_password(generate_otp()),  # Random password
                UserStatus=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Generate token
        access_token = create_access_token(data={"user_id": user.UserID})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "UserID": user.UserID,
                "UserName": user.UserIDcardrName,
                "UserEmail": user.Email,
                "UserStatus": user.UserStatus
            }
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )


@router.post("/facebook", response_model=TokenResponse)
async def facebook_login(request: FacebookAuthRequest, db: Session = Depends(get_db)):
    """Login with Facebook OAuth"""
    try:
        # Verify Facebook token
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://graph.facebook.com/me?fields=id,name,email&access_token={request.accessToken}"
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Facebook token"
                )
            
            fb_data = response.json()
            email = fb_data.get('email')
            name = fb_data.get('name', 'Facebook User')
            
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email not provided by Facebook"
                )
            
            # Check if user exists
            user = db.query(User).filter(User.Email == email).first()
            
            if not user:
                # Create new user
                user = User(
                    UserIDcardrName=name,
                    Email=email,
                    Password=hash_password(generate_otp()),  # Random password
                    UserStatus=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            
            # Generate token
            access_token = create_access_token(data={"user_id": user.UserID})
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "UserID": user.UserID,
                    "UserName": user.UserIDcardrName,
                    "UserEmail": user.Email,
                    "UserStatus": user.UserStatus
                }
            }
    
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to verify Facebook token"
        )


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user profile information"""
    try:
        # Update fields if provided
        if user_update.UserIDcardrName is not None:
            current_user.UserIDcardrName = user_update.UserIDcardrName
        
        if user_update.UserIDCardrNumber is not None:
            current_user.UserIDCardrNumber = user_update.UserIDCardrNumber
        
        if user_update.PhoneNumber is not None:
            current_user.PhoneNumber = user_update.PhoneNumber
        
        if user_update.Address is not None:
            current_user.Address = user_update.Address
        
        if user_update.DateOfBirth is not None:
            current_user.DateOfBirth = user_update.DateOfBirth
        
        # Commit changes
        db.commit()
        db.refresh(current_user)
        
        print(f"✅ Profile updated for user: {current_user.Email}")
        
        return current_user
    
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.put("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    try:
        # Verify current password
        if not verify_password(current_password, current_user.Password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters"
            )
        
        # Update password
        current_user.Password = hash_password(new_password)
        db.commit()
        
        print(f"✅ Password changed for user: {current_user.Email}")
        
        return {"message": "Password changed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error changing password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )


@router.put("/update-push-token")
async def update_push_token(
    token: str = None,
    enabled: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user's push notification token and preference"""
    try:
        current_user.PushToken = token
        current_user.IsNotificationsEnabled = enabled
        db.commit()
        return {"message": "Push settings updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update push settings: {str(e)}"
        )
