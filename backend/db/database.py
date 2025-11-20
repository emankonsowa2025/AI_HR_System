from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.models.user import Base
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./asktech.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
def init_db():
    """Initialize database and create tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")

# Dependency to get DB session
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
