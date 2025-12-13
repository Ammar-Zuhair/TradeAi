"""
Quick Fix Script - Copy All Required Models
============================================
This script copies all required model files from BackEnd to Trading System
to resolve import errors.
"""

import shutil
import os

# Source and destination
backend_models = r"d:\project\BackEnd\models"
trading_system = r"d:\project\Trading-System_First-main"

# Files to copy
files_to_copy = [
    "asset_type.py",
    "platform.py",
    "platform_server.py",
    "trading_pair.py",
    "account_symbol_mapping.py",
    "account.py",
    "trade.py",
    "transaction.py",
    "user.py",
    "enums.py"
]

print("\n" + "="*60)
print("🔧 COPYING MODEL FILES")
print("="*60)

for file in files_to_copy:
    src = os.path.join(backend_models, file)
    dst = os.path.join(trading_system, file)
    
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"✅ Copied: {file}")
    else:
        print(f"⚠️  Not found: {file}")

# Also copy database.py and security.py
other_files = [
    (r"d:\project\BackEnd\database.py", os.path.join(trading_system, "database.py")),
    (r"d:\project\BackEnd\security.py", os.path.join(trading_system, "security.py")),
    (r"d:\project\BackEnd\utils\account_helper.py", os.path.join(trading_system, "account_helper.py"))
]

for src, dst in other_files:
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"✅ Copied: {os.path.basename(src)}")

print("\n✅ All files copied successfully!")
print("="*60)
