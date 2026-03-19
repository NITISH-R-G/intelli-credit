import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os

# Add the parent directory to sys.path so we can import 'main'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

@pytest.mark.asyncio
async def test_health_check():
    """Test that the application health check endpoint returns correctly."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_secure_endpoint_no_token():
    """Test that the secure endpoint rejects requests without a token."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/secure-data")
    assert response.status_code == 401
    assert "detail" in response.json()
