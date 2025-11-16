from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Load local .env (has no effect on App Runner, but helps local dev)
load_dotenv()

# Get URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Safe fallback for App Runner import-time
if not DATABASE_URL:
    print("Warning from database.py: DATABASE_URL not set at import time.")
    # Use a local SQLite fallback so import doesn't crash
    DATABASE_URL = "sqlite:///./fallback.db"

# Create SQLAlchemy engine
# For SQLite, need special connect args
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # For PostgreSQL / Neon
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for ORM models
Base = declarative_base()

# Dependency used in routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

