"""
env_loader.py - Environment Variables Loader
============================================
Load MT5 credentials and configurations from .env file
Supports dual account setup for strategy comparison
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    """Configuration loaded from environment variables"""
    
    # Account 1 - Advanced Strategy
    MT5_LOGIN_ADVANCED = os.getenv('MT5_LOGIN_ADVANCED', '')
    MT5_PASSWORD_ADVANCED = os.getenv('MT5_PASSWORD_ADVANCED', '')
    MT5_SERVER_ADVANCED = os.getenv('MT5_SERVER_ADVANCED', '')
    
    # Account 2 - Simple Strategy
    MT5_LOGIN_SIMPLE = os.getenv('MT5_LOGIN_SIMPLE', '')
    MT5_PASSWORD_SIMPLE = os.getenv('MT5_PASSWORD_SIMPLE', '')
    MT5_SERVER_SIMPLE = os.getenv('MT5_SERVER_SIMPLE', '')
    
    # Legacy support (for single account Run_System.py)
    MT5_LOGIN = os.getenv('MT5_LOGIN', '')
    MT5_PASSWORD = os.getenv('MT5_PASSWORD', '')
    MT5_SERVER = os.getenv('MT5_SERVER', '')
    
    # Strategy Control
    ENABLE_ADVANCED_STRATEGY = os.getenv('ENABLE_ADVANCED_STRATEGY', 'true').lower() == 'true'
    ENABLE_SIMPLE_STRATEGY = os.getenv('ENABLE_SIMPLE_STRATEGY', 'true').lower() == 'true'
    
    # Trading Configuration
    SYMBOL = os.getenv('SYMBOL', 'XAUUSD')
    ENABLE_AUTO_TRADING = os.getenv('ENABLE_AUTO_TRADING', 'false').lower() == 'true'
    RISK_PERCENTAGE = float(os.getenv('RISK_PERCENTAGE', '1.0'))
    FVG_STRONG_THRESHOLD = int(os.getenv('FVG_STRONG_THRESHOLD', '60'))
    
    # Alerts
    ENABLE_SOUND_ALERT = os.getenv('ENABLE_SOUND_ALERT', 'true').lower() == 'true'
    ENABLE_LOG_FILE = os.getenv('ENABLE_LOG_FILE', 'true').lower() == 'true'
    
    # Scheduling
    CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '15'))
    REALTIME_CHECK_SECONDS = int(os.getenv('REALTIME_CHECK_SECONDS', '1'))
    NEWS_WINDOW_MINUTES = int(os.getenv('NEWS_WINDOW_MINUTES', '30'))

    
    @classmethod
    def validate_advanced(cls):
        """Validate Advanced account credentials"""
        if not cls.MT5_LOGIN_ADVANCED or not cls.MT5_PASSWORD_ADVANCED or not cls.MT5_SERVER_ADVANCED:
            raise ValueError(
                "Missing Advanced account MT5 credentials!\n"
                "Required: MT5_LOGIN_ADVANCED, MT5_PASSWORD_ADVANCED, MT5_SERVER_ADVANCED"
            )
        return True
    
    @classmethod
    def validate_simple(cls):
        """Validate Simple account credentials"""
        if not cls.MT5_LOGIN_SIMPLE or not cls.MT5_PASSWORD_SIMPLE or not cls.MT5_SERVER_SIMPLE:
            raise ValueError(
                "Missing Simple account MT5 credentials!\n"
                "Required: MT5_LOGIN_SIMPLE, MT5_PASSWORD_SIMPLE, MT5_SERVER_SIMPLE"
            )
        return True
    
    @classmethod
    def validate(cls):
        """Validate that required credentials are present (legacy single account)"""
        if not cls.MT5_LOGIN or not cls.MT5_PASSWORD or not cls.MT5_SERVER:
            raise ValueError(
                "Missing MT5 credentials! Please check your .env file.\n"
                "Required: MT5_LOGIN, MT5_PASSWORD, MT5_SERVER"
            )
        return True
    
    @classmethod
    def get_mt5_credentials(cls):
        """Get MT5 credentials as dictionary (legacy single account)"""
        cls.validate()
        return {
            'login': int(cls.MT5_LOGIN),
            'password': cls.MT5_PASSWORD,
            'server': cls.MT5_SERVER
        }
    
    @classmethod
    def get_advanced_credentials(cls):
        """Get Advanced account credentials"""
        cls.validate_advanced()
        return {
            'login': int(cls.MT5_LOGIN_ADVANCED),
            'password': cls.MT5_PASSWORD_ADVANCED,
            'server': cls.MT5_SERVER_ADVANCED
        }
    
    @classmethod
    def get_simple_credentials(cls):
        """Get Simple account credentials"""
        cls.validate_simple()
        return {
            'login': int(cls.MT5_LOGIN_SIMPLE),
            'password': cls.MT5_PASSWORD_SIMPLE,
            'server': cls.MT5_SERVER_SIMPLE
        }

    # Account 3 - Voting Strategy
    MT5_LOGIN_VOTING = os.getenv('MT5_LOGIN_VOTING', '')
    MT5_PASSWORD_VOTING = os.getenv('MT5_PASSWORD_VOTING', '')
    MT5_SERVER_VOTING = os.getenv('MT5_SERVER_VOTING', '')
    
    ENABLE_VOTING_STRATEGY = os.getenv('ENABLE_VOTING_STRATEGY', 'true').lower() == 'true'

    @classmethod
    def validate_voting(cls):
        """Validate Voting account credentials"""
        if not cls.MT5_LOGIN_VOTING or not cls.MT5_PASSWORD_VOTING or not cls.MT5_SERVER_VOTING:
            raise ValueError(
                "Missing Voting account MT5 credentials!\n"
                "Required: MT5_LOGIN_VOTING, MT5_PASSWORD_VOTING, MT5_SERVER_VOTING"
            )
        return True

    @classmethod
    def get_voting_credentials(cls):
        """Get Voting account credentials"""
        cls.validate_voting()
        return {
            'login': int(cls.MT5_LOGIN_VOTING),
            'password': cls.MT5_PASSWORD_VOTING,
            'server': cls.MT5_SERVER_VOTING
        }
