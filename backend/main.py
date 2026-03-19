from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from routers import analyze, cam, studio, applications, research, engine, execution, portfolio
from routers import policies as policies_router, decisions as decisions_router
from routers import approvals as approvals_router
import os
import uvicorn
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
import logging
from slowapi.errors import RateLimitExceeded
import redis.asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
from prometheus_fastapi_instrumentator import Instrumentator
import secure

from security.auth import verify_firebase_token

import logging
import structlog
from config import settings

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger(__name__)

# Load .env file if present (local development)
load_dotenv()

try:
    from async_database import async_engine, AsyncBase
    import async_models
    import db_models
except ImportError:
    async_engine = None
# ── Rate Limiter ─────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # ── Startup ──────────────────────────────────────────
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for d in ["data/raw", "data/curated", "data/features", "models"]:
        os.makedirs(os.path.join(base_dir, d), exist_ok=True)
        
    redis_url = settings.REDIS_URL
    redis = aioredis.from_url(redis_url, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    await FastAPILimiter.init(redis)
    logger.info("FastAPI Cache and Rate Limiter initialized with Redis.")

    yield
    # ── Shutdown ─────────────────────────────────────────
    # Clean up resources if needed


app = FastAPI(
    title="AI Credit Decisioning Engine API",
    description="Backend API for automated credit analysis and workflow execution.",
    version="2.1.0",
    lifespan=lifespan,
)

# ── Prometheus Metrics ───────────────────────────────────
Instrumentator().instrument(app).expose(app)

# ── Strict Security Headers ──────────────────────────────
secure_headers_dict = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "X-XSS-Protection": "1; mode=block"
}

@app.middleware("http")
async def set_secure_headers(request, call_next):
    response = await call_next(request)
    for key, value in secure_headers_dict.items():
        response.headers[key] = value
    return response


# ── Rate Limiting ────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ─────────────────────────────────────────────────
# Retrieve allowed origins from environment. If running in production, ensure strict domains are set.
allowed_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Idempotency Middleware ────────────────────────────────
try:
    from middleware.idempotency import IdempotencyMiddleware
    app.add_middleware(IdempotencyMiddleware)
except ImportError:
    pass  # graceful fallback if cachetools not installed

# ── Routers ──────────────────────────────────────────────
auth_dep = [Depends(verify_firebase_token)]

app.include_router(analyze.router, prefix="/api", tags=["Analysis"])
app.include_router(analyze.router, prefix="/api", tags=["Analysis"])
from routers import health
app.include_router(health.router)
app.include_router(cam.router, prefix="/api/cam", tags=["CAM Generation"], dependencies=auth_dep)
app.include_router(applications.router, prefix="/api", tags=["Applications"], dependencies=auth_dep)
app.include_router(research.router, prefix="/api", tags=["Research"], dependencies=auth_dep)
app.include_router(portfolio.router, prefix="/api", tags=["Portfolio"], dependencies=auth_dep)
app.include_router(engine.router, prefix="/api/v1/engine", tags=["Engine Deployment"], dependencies=auth_dep)
app.include_router(execution.router, prefix="/api/v1/engine/execute", tags=["Engine Execution"], dependencies=auth_dep)

# v2 Policy Engine & Decision Routers (async PostgreSQL)
app.include_router(policies_router.router, prefix="/api/v2", tags=["Policy Engine"], dependencies=auth_dep)
app.include_router(decisions_router.router, prefix="/api/v2", tags=["Decision Engine"], dependencies=auth_dep)
app.include_router(approvals_router.router, prefix="/api/v2", tags=["Maker-Checker Approvals"], dependencies=auth_dep)



@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Credit Engine API",
        "version": "2.1.0",
        "environment": os.environ.get("ENVIRONMENT", "production"),
    }


@app.get("/api/secure-data", dependencies=[Depends(verify_firebase_token)])
async def secure_endpoint():
    """Example of a route protected by Firebase Authentication."""
    return {"message": "You are securely authenticated via Firebase!"}


if __name__ == "__main__":
    logger.info("Starting AI Credit Decisioning API...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.environ.get("ENVIRONMENT", "production") == "development",
    )
