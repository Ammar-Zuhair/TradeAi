from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.transaction import Transaction
from models.account import Account
from models.user import User
from schemas.transaction import TransactionCreate, TransactionResponse
from utils.dependencies import get_current_user

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new transaction"""
    # Verify account exists
    account = db.query(Account).filter(Account.AccountID == transaction.AccountID).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # ✅ Create new transaction with integer enums
    # TransactionType: 1=Month, 2=3Months, 3=6Months, 4=Year
    # TransactionStatus: 1=Completed, 2=Pending, 3=Failed (default=2)
    new_transaction = Transaction(
        AccountID=transaction.AccountID,
        TransactionType=transaction.TransactionType,  # ✅ Integer from schema
        TransactionAmount=transaction.TransactionAmount,  # ✅ Correct field name
        TransactionStatus=2  # ✅ Default to Pending
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    return new_transaction


@router.get("", response_model=List[TransactionResponse])
async def get_all_transactions(
    account_id: Optional[int] = Query(None, alias="accountID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all transactions, optionally filter by account ID"""
    query = db.query(Transaction)
    
    if account_id is not None:
        query = query.filter(Transaction.AccountID == account_id)
    
    transactions = query.all()
    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get transaction by ID"""
    transaction = db.query(Transaction).filter(Transaction.TransactionID == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return transaction
