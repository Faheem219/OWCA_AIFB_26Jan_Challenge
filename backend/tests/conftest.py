"""
Test configuration and fixtures.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from app.main import app
from app.core.config import settings
from app.db.mongodb import mongodb
from app.db.redis import redis_cache

# Test database settings
TEST_MONGODB_URL = "mongodb://localhost:27017"
TEST_MONGODB_DATABASE = "multilingual_mandi_test"
TEST_REDIS_URL = "redis://localhost:6379/1"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """Create test database connection."""
    client = AsyncIOMotorClient(TEST_MONGODB_URL)
    database = client[TEST_MONGODB_DATABASE]
    
    yield database
    
    # Cleanup: drop test database
    await client.drop_database(TEST_MONGODB_DATABASE)
    client.close()


@pytest.fixture(scope="session")
async def test_redis():
    """Create test Redis connection."""
    redis_client = redis.from_url(TEST_REDIS_URL, decode_responses=True)
    
    yield redis_client
    
    # Cleanup: flush test database
    await redis_client.flushdb()
    await redis_client.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "phone": "+919876543210",
        "password": "testpassword123",
        "full_name": "Test User",
        "preferred_language": "en",
        "user_type": "vendor",
        "vendor_profile": {
            "business_name": "Test Business",
            "business_type": "agriculture",
            "specializations": ["rice", "wheat"],
            "location": {
                "address": "123 Test Street",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400001"
            },
            "languages_spoken": ["en", "hi", "mr"]
        }
    }


@pytest.fixture
async def authenticated_user_token(client: AsyncClient, test_user_data):
    """Create a user and return authentication token."""
    # Register user
    response = await client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 200
    
    # Login user
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    token_data = response.json()["data"]
    return token_data["access_token"]