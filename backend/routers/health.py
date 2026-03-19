from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from dependencies import get_db_session
from config import settings
import redis.asyncio as redis
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/live", summary="Liveness Probe")
async def liveness_probe():
    """Returns 200 OK instantly. Best for Kubernetes liveness/Docker healthcheck."""
    return {"status": "ok", "service": "intelli-credit-backend"}

@router.get("/ready", summary="Readiness Probe")
async def readiness_probe(db: AsyncSession = Depends(get_db_session)):
    """Async ping to Postgres and Redis to ensure readiness."""
    errors = {}
    
    # Check Database
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Readiness probe failed on database: {str(e)}")
        errors["database"] = "unreachable"

    # Check Redis
    try:
        r = redis.from_url(str(settings.REDIS_URL))
        await r.ping()
        await r.aclose()
    except Exception as e:
        logger.error(f"Readiness probe failed on Redis: {str(e)}")
        errors["redis"] = "unreachable"

    if errors:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "errors": errors}
        )

    return {"status": "ready"}
