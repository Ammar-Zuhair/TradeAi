from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Encryption settings
ENCRYPTION_KEY = bytes.fromhex(os.getenv("ENCRYPTION_KEY", "0" * 64))

# In-memory OTP storage (in production, use Redis)
otp_store = {}


# Password hashing functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # bcrypt has a limit of 72 bytes
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes and decode back to string (ignoring errors if split mid-char)
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # bcrypt has a limit of 72 bytes
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
        
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"⚠️ Password verification error: {str(e)}")
        return False


# AES Encryption/Decryption for broker credentials
def encrypt(text: str) -> str:
    """Encrypt text using AES-256-CBC"""
    if not text:
        return None
    
    iv = os.urandom(16)
    cipher = Cipher(
        algorithms.AES(ENCRYPTION_KEY),
        modes.CBC(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    
    # Pad the text to be multiple of 16 bytes
    padding_length = 16 - (len(text) % 16)
    padded_text = text + (chr(padding_length) * padding_length)
    
    encrypted = encryptor.update(padded_text.encode()) + encryptor.finalize()
    
    return iv.hex() + ':' + encrypted.hex()


def decrypt(text: str) -> str:
    """Decrypt text using AES-256-CBC"""
    if not text:
        return None
    
    parts = text.split(':')
    iv = bytes.fromhex(parts[0])
    encrypted_text = bytes.fromhex(parts[1])
    
    cipher = Cipher(
        algorithms.AES(ENCRYPTION_KEY),
        modes.CBC(iv),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    
    decrypted = decryptor.update(encrypted_text) + decryptor.finalize()
    
    # Remove padding
    padding_length = decrypted[-1]
    decrypted = decrypted[:-padding_length]
    
    return decrypted.decode()


# JWT token functions
def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# OTP functions
def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return str(secrets.randbelow(900000) + 100000)


def store_otp(email: str, otp: str):
    """Store OTP with 5-minute expiry"""
    email = email.lower().strip()  # Normalize email
    expiry = datetime.utcnow() + timedelta(minutes=5)
    otp_store[email] = {
        'otp': otp,
        'expiry': expiry,
        'attempts': 0
    }
    print(f"💾 OTP Stored for {email}: {otp} (Expires: {expiry})")


def verify_otp(email: str, otp: str) -> dict:
    """Verify OTP"""
    email = email.lower().strip()  # Normalize email
    
    print(f"🔍 Verifying OTP for {email}")
    print(f"📥 Received OTP: '{otp}'")
    
    if email not in otp_store:
        print(f"❌ No OTP found for {email}")
        print(f"📂 Current Store Keys: {list(otp_store.keys())}")
        return {'valid': False, 'message': 'No OTP found for this email'}
    
    stored = otp_store[email]
    print(f"💾 Stored OTP: '{stored['otp']}'")
    print(f"⏳ Expiry: {stored['expiry']} (Current: {datetime.utcnow()})")
    
    # Check expiry
    if datetime.utcnow() > stored['expiry']:
        print(f"❌ OTP expired")
        del otp_store[email]
        return {'valid': False, 'message': 'OTP has expired'}
    
    # Check attempts
    if stored['attempts'] >= 3:
        print(f"❌ Too many attempts")
        del otp_store[email]
        return {'valid': False, 'message': 'Too many failed attempts'}
    
    # Verify OTP
    if stored['otp'] == otp:
        print(f"✅ OTP Verified Successfully")
        del otp_store[email]
        return {'valid': True, 'message': 'OTP verified successfully'}
    else:
        stored['attempts'] += 1
        print(f"❌ OTP Mismatch (Attempts: {stored['attempts']})")
        return {'valid': False, 'message': 'Invalid OTP'}


def clear_otp(email: str):
    """Clear OTP for email"""
    if email in otp_store:
        del otp_store[email]
