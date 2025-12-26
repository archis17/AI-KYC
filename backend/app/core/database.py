from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Use psycopg3 driver (SQLAlchemy 2.0 will auto-detect psycopg3 if installed)
# For explicit driver, replace postgresql:// with postgresql+psycopg://
# This works with both local PostgreSQL and cloud databases like Neon
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://") and "+" not in database_url:
    # Only replace if no driver is already specified
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

