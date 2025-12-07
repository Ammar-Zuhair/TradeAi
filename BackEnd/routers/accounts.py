from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.account import Account
from models.user import User
from schemas.account import AccountCreate, AccountUpdate, AccountResponse, MT5VerificationResponse
from utils.dependencies import get_current_user
from utils.security import encrypt
from utils.mt5_service import MT5Service

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.post("", response_model=MT5VerificationResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new trading account with MT5 verification
    
    This endpoint:
    1. Verifies MT5 account credentials
    2. Fetches account information (balance, equity, etc.)
    3. Saves the account to database
    4. Returns detailed verification results
    """
    # Verify user exists
    user = db.query(User).filter(User.UserID == account.UserID).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify required MT5 credentials
    if not account.AccountLoginNumber or not account.AccountLoginPassword or not account.AccountLoginServer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MT5 login credentials (number, password, server) are required"
        )
    
    # Verify MT5 account and fetch information
    success, mt5_data, error = MT5Service.verify_and_get_account_info(
        login=account.AccountLoginNumber,
        password=account.AccountLoginPassword,
        server=account.AccountLoginServer
    )
    
    if not success:
        return MT5VerificationResponse(
            success=False,
            message=f"MT5 verification failed: {error}",
            account=None,
            mt5_info=None
        )
    
    # Determine account type from MT5 data
    account_type = mt5_data.get('trade_mode', 'Unknown')
    
    # Create new account with verified data
    new_account = Account(
        UserID=account.UserID,
        AccountType=account_type,
        AccountLoginServer=account.AccountLoginServer,
        AccountLoginNumber=account.AccountLoginNumber,
        AccountLoginPassword=encrypt(account.AccountLoginPassword),
        AccountBalance=mt5_data.get('balance', 0.00),
        RiskPercentage=account.RiskPercentage if account.RiskPercentage else 1.00,
        TradingStrategy=account.TradingStrategy if account.TradingStrategy else "All"
    )
    
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    return MT5VerificationResponse(
        success=True,
        message=f"Account verified and added successfully! Balance: ${mt5_data.get('balance', 0):.2f}",
        account=new_account,
        mt5_info={
            "balance": mt5_data.get('balance'),
            "equity": mt5_data.get('equity'),
            "margin": mt5_data.get('margin'),
            "margin_free": mt5_data.get('margin_free'),
            "profit": mt5_data.get('profit'),
            "leverage": mt5_data.get('leverage'),
            "currency": mt5_data.get('currency'),
            "company": mt5_data.get('company'),
            "server": mt5_data.get('server')
        }
    )


@router.get("", response_model=List[AccountResponse])
async def get_all_accounts(
    user_id: Optional[int] = Query(None, alias="userID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all accounts, optionally filter by user ID"""
    query = db.query(Account)
    
    if user_id is not None:
        query = query.filter(Account.UserID == user_id)
    
    accounts = query.all()
    return accounts


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get account by ID"""
    account = db.query(Account).filter(Account.AccountID == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_update: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update account"""
    account = db.query(Account).filter(Account.AccountID == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Update fields
    if account_update.AccountType is not None:
        account.AccountType = account_update.AccountType
    if account_update.AccountLoginServer is not None:
        account.AccountLoginServer = account_update.AccountLoginServer
    if account_update.AccountLoginNumber is not None:
        account.AccountLoginNumber = account_update.AccountLoginNumber
    if account_update.AccountLoginPassword is not None:
        account.AccountLoginPassword = encrypt(account_update.AccountLoginPassword)
    if account_update.AccountBalance is not None:
        account.AccountBalance = account_update.AccountBalance
    if account_update.RiskPercentage is not None:
        account.RiskPercentage = account_update.RiskPercentage
    if account_update.TradingStrategy is not None:
        account.TradingStrategy = account_update.TradingStrategy
    
    db.commit()
    db.refresh(account)
    
    return account


@router.delete("/{account_id}")
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete account"""
    account = db.query(Account).filter(Account.AccountID == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    db.delete(account)
    db.commit()
    
    return {"message": "Account deleted successfully"}
