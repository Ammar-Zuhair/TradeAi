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
    if not account.AccountLoginNumber or not account.AccountLoginPassword:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MT5 login credentials (number, password) are required"
        )
    
    if not account.ServerID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ServerID is required"
        )
    
    # ✅ Get server name and ID
    from models.broker_server import BrokerServer
    server = db.query(BrokerServer).filter(BrokerServer.ServerID == account.ServerID).first()
    
    if not server:
         raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
             detail=f"Server with ID {account.ServerID} not found"
         )
        
    server_name = server.ServerName
    
    server_name = server.ServerName
            
    # Verify MT5 account and fetch information
    success, mt5_data, error = MT5Service.verify_and_get_account_info(
        login=account.AccountLoginNumber,
        password=account.AccountLoginPassword,
        server=server_name 
    )
    
    if not success:
        return MT5VerificationResponse(
            success=False,
            message=f"MT5 verification failed: {error}",
            account=None,
            mt5_info=None
        )
        
    # If verification success and we didn't have a server record, create/find it now
    # STRICT MODE: Server MUST exist via ServerID beforehand. 
            
    # Ensure account.ServerID is set for the DB
    account.ServerID = server.ServerID
    server_name = server.ServerName
    
    if not success:
        return MT5VerificationResponse(
            success=False,
            message=f"MT5 verification failed: {error}",
            account=None,
            mt5_info=None
        )
    
    # ✅ Convert AccountType from MT5 trade_mode to Integer enum
    # MT5 trade_mode: 0=Disabled, 1=LongOnly, 2=ShortOnly, 3=CloseOnly, 4=Full
    # We determine Demo/Real from account info
    account_type_int = 2  # Default to Real
    
    # Check if it's a demo account (usually has "demo" in server name or company)
    server_lower = server_name.lower()
    company_lower = mt5_data.get('company', '').lower()
    
    if 'demo' in server_lower or 'demo' in company_lower or 'trial' in server_lower:
        account_type_int = 1  # Demo
    
    # Create new account with verified data
    new_account = Account(
        UserID=account.UserID,
        AccountType=account_type_int,  # ✅ Integer: 1=Demo, 2=Real
        ServerID=account.ServerID,  # ✅ Link to PlatformServers table
        AccountLoginNumber=account.AccountLoginNumber,
        AccountLoginPassword=encrypt(account.AccountLoginPassword),
        AccountBalance=mt5_data.get('balance', 0.00),
        RiskPercentage=account.RiskPercentage if account.RiskPercentage else 1.00,
        TradingStrategy=account.TradingStrategy if account.TradingStrategy else "All",
        AccountName=account.AccountName  # ✅ User-friendly account name
    )
    
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    # ✅ Automatically create symbol mappings
    try:
        from utils.mt5_symbols import get_mt5_symbols, suggest_symbol_mapping, create_symbol_mappings
        
        # Get available symbols from MT5
        symbols = get_mt5_symbols(
            login=account.AccountLoginNumber,
            password=account.AccountLoginPassword,
            server=server_name
        )
        
        if symbols:
            # Get automatic mapping suggestions
            # suggestions is now a list of dicts: [{'account_symbol': '...', 'suggested_trading_pair_id': ...}]
            suggestions = suggest_symbol_mapping(new_account.AccountID, symbols)
            
            if suggestions:
                # Create mappings automatically
                mapping_dicts = [
                    {
                        'account_symbol': s['account_symbol'],
                        'trading_pair_id': s['suggested_trading_pair_id']
                    }
                    for s in suggestions if s['suggested_trading_pair_id']
                ]
                
                if mapping_dicts:
                    success = create_symbol_mappings(new_account.AccountID, mapping_dicts)
                    if success:
                        print(f"✅ Created {len(mapping_dicts)} symbol mappings automatically")
                    else:
                        print("⚠️ Failed to create some symbol mappings")
        else:
            print("⚠️ Could not fetch MT5 symbols for automatic mapping")
            
    except Exception as e:
        print(f"⚠️ Symbol mapping creation failed (non-critical): {e}")
        # Don't fail the account creation if symbol mapping fails
    
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all accounts for the current user"""
    # STRICT SECURITY: Only return accounts belonging to the authenticated user
    # Do NOT rely on client-provided UserID
    from models.broker_server import BrokerServer
    from sqlalchemy.orm import joinedload
    
    accounts = db.query(Account).options(
        joinedload(Account.server)
    ).filter(
        Account.UserID == current_user.UserID
    ).all()
    
    # Manually populate the ServerName field from the relationship
    result = []
    for acc in accounts:
        # Create a dict from the model
        acc_dict = {c.name: getattr(acc, c.name) for c in acc.__table__.columns}
        
        # Add ServerName if server exists
        if acc.server:
            acc_dict['ServerName'] = acc.server.ServerName
        else:
            acc_dict['ServerName'] = "Unknown"
            
        result.append(acc_dict)
        
    return result


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get account by ID"""
    from sqlalchemy.orm import joinedload
    
    account = db.query(Account).options(
        joinedload(Account.server)
    ).filter(Account.AccountID == account_id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
        
    # Create response dict
    acc_dict = {c.name: getattr(account, c.name) for c in account.__table__.columns}
    if account.server:
        acc_dict['ServerName'] = account.server.ServerName
    else:
        acc_dict['ServerName'] = "Unknown"
        
    return acc_dict


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
