from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# The engine is the actual connection to PostgreSQL
engine = create_engine(settings.DATABASE_URL)

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