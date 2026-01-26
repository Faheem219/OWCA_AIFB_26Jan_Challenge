"""
Pytest configuration and fixtures for the Multilingual Mandi Marketplace tests.
"""

import os
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis

# Set test environment before importing app
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017/test_mandi_marketplace")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("JWT_SECRET_KEY", "test_jwt_secret_key_for_testing_only_not_for_production")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test_access_key")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test_secret_key")
os.environ.setdefault("AGMARKNET_API_KEY", "test_agmarknet_key")
os.environ.setdefault("RAZORPAY_KEY_ID", "test_razorpay_key")
os.environ.setdefault("RAZORPAY_KEY_SECRET", "test_razorpay_secret")
os.environ.setdefault("UPI_MERCHANT_ID", "test_upi_merchant")

from app.main import app
from app.core.config import settings
from app.core.database import get_database
from app.core.redis import get_redis


# Test database settings
TEST_MONGODB_URL = "mongodb://localhost:27017/test_mandi_marketplace"
TEST_REDIS_URL = "redis://localhost:6379/1"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_mongo_client() -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Create a test MongoDB client."""
    client = AsyncIOMotorClient(TEST_MONGODB_URL)
    yield client
    client.close()


@pytest_asyncio.fixture(scope="session")
async def test_redis_client() -> AsyncGenerator[redis.Redis, None]:
    """Create a test Redis client."""
    client = redis.from_url(TEST_REDIS_URL, decode_responses=True)
    yield client
    await client.close()


@pytest_asyncio.fixture
async def test_db(test_mongo_client: AsyncIOMotorClient):
    """Create a test database and clean it up after each test."""
    db = test_mongo_client.test_mandi_marketplace
    
    # Clean up before test
    await db.drop_collection("users")
    await db.drop_collection("products")
    await db.drop_collection("conversations")
    await db.drop_collection("messages")
    await db.drop_collection("transactions")
    await db.drop_collection("market_prices")
    
    yield db
    
    # Clean up after test
    await db.drop_collection("users")
    await db.drop_collection("products")
    await db.drop_collection("conversations")
    await db.drop_collection("messages")
    await db.drop_collection("transactions")
    await db.drop_collection("market_prices")


@pytest_asyncio.fixture
async def test_cache(test_redis_client: redis.Redis):
    """Create a test Redis cache and clean it up after each test."""
    # Clean up before test
    await test_redis_client.flushdb()
    
    yield test_redis_client
    
    # Clean up after test
    await test_redis_client.flushdb()


@pytest_asyncio.fixture
async def client(test_db, test_cache) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client."""
    
    # Override database and cache dependencies
    app.dependency_overrides[get_database] = lambda: test_db
    app.dependency_overrides[get_redis] = lambda: test_cache
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user_data():
    """Mock user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "role": "BUYER",
        "preferred_languages": ["en", "hi"],
        "location": {
            "type": "Point",
            "coordinates": [77.2090, 28.6139],
            "address": "New Delhi, India"
        }
    }


@pytest.fixture
def mock_vendor_data():
    """Mock vendor data for testing."""
    return {
        "email": "vendor@example.com",
        "password": "vendorpassword123",
        "role": "VENDOR",
        "preferred_languages": ["en", "hi"],
        "business_name": "Test Vendor",
        "business_type": "Agriculture",
        "product_categories": ["VEGETABLES", "FRUITS"],
        "location": {
            "type": "Point",
            "coordinates": [77.2090, 28.6139],
            "address": "New Delhi, India"
        }
    }


@pytest.fixture
def mock_product_data():
    """Mock product data for testing."""
    return {
        "name": {
            "original_language": "en",
            "original_text": "Fresh Tomatoes",
            "translations": {},
            "auto_translated": False
        },
        "description": {
            "original_language": "en",
            "original_text": "Fresh red tomatoes from local farm",
            "translations": {},
            "auto_translated": False
        },
        "category": "VEGETABLES",
        "subcategory": "tomato",
        "base_price": 50.0,
        "unit": "kg",
        "quantity_available": 100,
        "quality_grade": "A",
        "location": {
            "type": "Point",
            "coordinates": [77.2090, 28.6139],
            "address": "New Delhi, India"
        },
        "tags": ["fresh", "organic", "local"]
    }


@pytest.fixture
def mock_translation_request():
    """Mock translation request data for testing."""
    return {
        "text": "Hello, how are you?",
        "source_language": "en",
        "target_language": "hi"
    }


@pytest.fixture
def mock_price_data():
    """Mock market price data for testing."""
    return {
        "commodity": "tomato",
        "market": "Delhi",
        "date": "2024-01-01",
        "min_price": 40.0,
        "max_price": 60.0,
        "modal_price": 50.0,
        "arrivals": 1000,
        "source": "agmarknet"
    }


# Property-based testing fixtures
@pytest.fixture
def pbt_user_strategy():
    """Hypothesis strategy for generating user data."""
    from hypothesis import strategies as st
    
    return st.fixed_dicts({
        "email": st.emails(),
        "role": st.sampled_from(["VENDOR", "BUYER"]),
        "preferred_languages": st.lists(
            st.sampled_from(["hi", "en", "ta", "te", "kn", "ml", "gu", "pa", "bn", "mr"]),
            min_size=1,
            max_size=3,
            unique=True
        ),
        "location": st.fixed_dicts({
            "type": st.just("Point"),
            "coordinates": st.lists(
                st.floats(min_value=-180, max_value=180),
                min_size=2,
                max_size=2
            )
        })
    })


@pytest.fixture
def pbt_product_strategy():
    """Hypothesis strategy for generating product data."""
    from hypothesis import strategies as st
    
    return st.fixed_dicts({
        "name": st.text(min_size=1, max_size=100),
        "category": st.sampled_from(["VEGETABLES", "FRUITS", "GRAINS", "SPICES", "DAIRY"]),
        "base_price": st.floats(min_value=1.0, max_value=10000.0),
        "quantity_available": st.integers(min_value=1, max_value=1000),
        "unit": st.sampled_from(["kg", "gram", "liter", "piece", "dozen"])
    })


# Async test helpers
async def create_test_user(client: AsyncClient, user_data: dict):
    """Helper function to create a test user."""
    response = await client.post("/api/v1/auth/register", json=user_data)
    return response


async def authenticate_user(client: AsyncClient, email: str, password: str):
    """Helper function to authenticate a user and return tokens."""
    response = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    return response


def get_auth_headers(token: str) -> dict:
    """Helper function to get authorization headers."""
    return {"Authorization": f"Bearer {token}"}


# Markers for different test types
pytestmark = [
    pytest.mark.asyncio,
]