"""
Check Account Credentials in Database
======================================
This script checks the account credentials stored in the database
and verifies if they can connect to MT5.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'BackEnd'))

from database import SessionLocal
from account import Account
from user import User  # ✅ Required for SQLAlchemy relationships
from security import decrypt
import MetaTrader5 as mt5
from platform_server import PlatformServer
from platformModel import Platform

def check_accounts():
    db = SessionLocal()
    
    try:
        print("\n" + "="*60)
        print("🔍 CHECKING ACCOUNT CREDENTIALS")
        print("="*60)
        
        accounts = db.query(Account).all()
        
        print(f"\n📊 Found {len(accounts)} accounts in database\n")
        
        for account in accounts:
            print(f"\n{'='*60}")
            print(f"Account ID: {account.AccountID}")
            print(f"Login: {account.AccountLoginNumber}")
            print(f"Server: {account.AccountLoginServer}")
            print(f"Strategy: {account.TradingStrategy}")
            print(f"Account Type: {account.AccountType}")
            
            # Try to decrypt password
            try:
                password = decrypt(account.AccountLoginPassword)
                print(f"Password: {'*' * len(password)} (decrypted successfully)")
            except Exception as e:
                print(f"❌ Password decryption failed: {e}")
                continue
            
            # Try to connect to MT5
            print(f"\n🔌 Attempting MT5 connection...")
            
            if not mt5.initialize():
                print(f"❌ MT5 initialization failed: {mt5.last_error()}")
                continue
            
            authorized = mt5.login(
                login=account.AccountLoginNumber,
                password=password,
                server=account.AccountLoginServer
            )
            
            if authorized:
                account_info = mt5.account_info()
                print(f"✅ Connection successful!")
                print(f"   Balance: ${account_info.balance}")
                print(f"   Equity: ${account_info.equity}")
                print(f"   Company: {account_info.company}")
            else:
                error = mt5.last_error()
                print(f"❌ Connection failed!")
                print(f"   Error Code: {error[0]}")
                print(f"   Error Message: {error[1]}")
                
                # Common error codes
                if error[0] == -6:
                    print(f"   💡 Suggestion: Check password - Authorization failed")
                elif error[0] == -7:
                    print(f"   💡 Suggestion: Disable OTP/2FA on this account")
                elif error[0] == -10:
                    print(f"   💡 Suggestion: Check server name")
            
            mt5.shutdown()
        
        print("\n" + "="*60)
        
    finally:
        db.close()

if __name__ == "__main__":
    check_accounts()
