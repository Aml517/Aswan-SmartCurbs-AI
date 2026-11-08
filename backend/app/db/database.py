import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///./"):
    backend_dir = Path(__file__).resolve().parent.parent.parent
    canonical_db = (backend_dir / db_url.replace("sqlite:///./", "")).resolve()
    db_url = f"sqlite:///{canonical_db.as_posix()}"

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
engine = create_engine(db_url, connect_args=connect_args)

# Each request gets its own session (database conversation)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All models must inherit from this Base
# This is how SQLAlchemy knows which tables to create
Base = declarative_base()


def get_db():
    """
    FastAPI dependency — provides a database session to each API endpoint.
    Automatically closes the session when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()