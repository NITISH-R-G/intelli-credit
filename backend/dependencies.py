from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from async_database import AsyncSessionLocal as async_session

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to provide a safely bounded async database session per request."""
    async with async_session() as session:
        yield session
