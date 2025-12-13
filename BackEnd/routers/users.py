from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from typing import List

from database import get_db
from models.user import User

from schemas.user import UserCreate, UserUpdate, UserResponse

from utils.dependencies import get_current_user

from utils.security import hash_password


router = APIRouter(prefix="/api/users", tags=["Users"])



@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)

async def create_user(

    user: UserCreate,

    db: Session = Depends(get_db)

):

    """Create a new user"""

    # Check if email already exists

    existing_user = db.query(User).filter(User.Email == user.Email).first()

    if existing_user:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail="Email already registered"
        )
    

    # Create new user

    new_user = User(

        Email=user.Email,

        Password=hash_password(user.Password),

        UserStatus=True,

        UserIDCardNumber=user.UserIDCardNumber,

        PhoneNumber=user.PhoneNumber,

        Address=user.Address,

        DateOfBirth=user.DateOfBirth
    )
    

    db.add(new_user)

    db.commit()

    db.refresh(new_user)
    

    return new_user



@router.get("", response_model=List[UserResponse])

async def get_all_users(

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)

):

    """Get all users"""

    users = db.query(User).all()
    return users



@router.get("/{user_id}", response_model=UserResponse)

async def get_user(

    user_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)

):

    """Get user by ID"""

    user = db.query(User).filter(User.UserID == user_id).first()

    if not user:

        raise HTTPException(

            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user



@router.put("/{user_id}", response_model=UserResponse)

async def update_user(

    user_id: int,

    user_update: UserUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)

):
    """Update user"""

    user = db.query(User).filter(User.UserID == user_id).first()

    if not user:

        raise HTTPException(

            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    

    # Update fields
    if user_update.UserIDCardName is not None:
        user.UserIDCardName = user_update.UserIDCardName
    if user_update.Email is not None:
        # Check if new email already exists
        existing = db.query(User).filter(
            User.Email == user_update.Email,
            User.UserID != user_id
        ).first()

        if existing:

            raise HTTPException(

                status_code=status.HTTP_400_BAD_REQUEST,

                detail="Email already in use"
            )

        user.Email = user_update.Email

    if user_update.Password is not None:

        user.Password = hash_password(user_update.Password)

    if user_update.UserStatus is not None:

        user.UserStatus = user_update.UserStatus

    if user_update.UserIDCardNumber is not None:

        user.UserIDCardNumber = user_update.UserIDCardNumber

    if user_update.PhoneNumber is not None:

        user.PhoneNumber = user_update.PhoneNumber

    if user_update.Address is not None:

        user.Address = user_update.Address

    if user_update.DateOfBirth is not None:

        user.DateOfBirth = user_update.DateOfBirth
    

    db.commit()

    db.refresh(user)
    
    return user



@router.delete("/{user_id}")

async def delete_user(

    user_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)

):

    """Delete user"""

    user = db.query(User).filter(User.UserID == user_id).first()

    if not user:

        raise HTTPException(

            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    

    db.delete(user)

    db.commit()
    

    return {"message": "User deleted successfully"}

