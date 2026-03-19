import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# It uses the same database, but with the synchronous driver (psycopg2 instead of asyncpg)
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/intelli_credit"
)

# Convert asyncpg URL to standard sync postgresql URL if needed
sync_url = DATABASE_URL.replace("+asyncpg", "+psycopg")

# Create synchronous engine
engine = create_engine(sync_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
