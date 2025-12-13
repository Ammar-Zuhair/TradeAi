"""
Enums for database integer fields
"""
from enum import IntEnum


class AccountTypeEnum(IntEnum):
    """Account type enumeration"""
    DEMO = 1
    REAL = 2


class TransactionTypeEnum(IntEnum):
    """Transaction type enumeration (subscription periods)"""
    MONTH_1 = 1      # 1 month
    MONTHS_3 = 2     # 3 months
    MONTHS_6 = 3     # 6 months
    YEAR_1 = 4       # 1 year


class TransactionStatusEnum(IntEnum):
    """Transaction status enumeration"""
    COMPLETED = 1
    PENDING = 2
    FAILED = 3


class TradeTypeEnum(IntEnum):
    """Trade type enumeration"""
    BUY = 1
    SELL = 2


class TradeStatusEnum(IntEnum):
    """Trade status enumeration"""
    OPEN = 1
    WINNING = 2
    LOSING = 3
