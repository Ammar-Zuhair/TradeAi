from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

print(f"\n{'='*60}")
print(f"DATABASE CONFIGURATION")
print(f"{'='*60}")
print(f"Database: {DB_NAME}")
print(f"Host: {DB_HOST}")
print(f"User: {DB_USER}")
print(f"URL: postgresql://{DB_USER}:****@{DB_HOST}/{DB_NAME}")
print(f"{'='*60}\n")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20
)

print(f"Database engine created successfully")
print(f"Connection pool: size={10}, max_overflow={20}\n")

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    print(f"Database session created")
    try:
        yield db
    finally:
        db.close()
        print(f"Database session closed")
