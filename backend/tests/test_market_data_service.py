"""
Unit tests for market data service.

Tests the market data integration, validation, and caching functionality.
"""

import pytest
import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.market_data_service import MarketDataService
from app.models.market_data import (
    MarketPrice, MarketPriceRequest, DataSource, DataQuality, PriceUnit,
    AgmarknetApiResponse, DataValidationResult
)


@pytest.fixture
async def mock_database():
    """Mock database for testing."""
    database = MagicMock()
    database.market_prices = AsyncMock()
    database.price_history = AsyncMock()
    database.data_sync_status = AsyncMock()
    return database


@pytest.fixture
async def market_data_service(mock_database):
    """Create market data service for testing."""
    service = MarketDataService(mock_database)
    service.redis_client = AsyncMock()
    service.http_client = AsyncMock()
    return service


@pytest.fixture
def sample_market_price():
    """Sample market price data for testing."""
    return MarketPrice(
        commodity="onion",
        variety="red",
        market="Delhi",
        state="Delhi",
        district="New Delhi",
        min_price=Decimal("20.00"),
        max_price=Decimal("30.00"),
        modal_price=Decimal("25.00"),
        unit=PriceUnit.PER_KG,
        arrivals=100,
        arrivals_unit="quintal",
        date=date.today(),
        source=DataSource.AGMARKNET,
        data_quality=DataQuality.HIGH
    )


@pytest.fixture
def sample_agmarknet_response():
    """Sample Agmarknet API response for testing."""
    return {
        "status": "ok",
        "total": 1,
        "count": 1,
        "records": [
            {
                "commodity": "onion",
                "variety": "red",
                "market": "Delhi",
                "state": "Delhi",
                "district": "New Delhi",
                "min_price": "20.00",
                "max_price": "30.00",
                "modal_price": "25.00",
                "arrivals": "100",
                "date": date.today().strftime("%Y-%m-%d")
            }
        ]
    }


class TestMarketDataService:
    """Test cases for MarketDataService."""
    
    @pytest.mark.asyncio
    async def test_validate_market_data_valid(self, market_data_service, sample_market_price):
        """Test validation of valid market data."""
        result = await market_data_service.validate_market_data(sample_market_price)
        
        assert result.is_valid is True
        assert result.quality_score >= 0.8
        assert len(result.issues) == 0
        assert all(result.validation_checks.values())
    
    @pytest.mark.asyncio
    async def test_validate_market_data_invalid_prices(self, market_data_service):
        """Test validation of market data with invalid prices."""
        invalid_price = MarketPrice(
            commodity="onion",
            market="Delhi",
            state="Delhi",
            min_price=Decimal("30.00"),  # Min > Max (invalid)
            max_price=Decimal("20.00"),
            modal_price=Decimal("25.00"),
            unit=PriceUnit.PER_KG,
            date=date.today(),
            source=DataSource.AGMARKNET
        )
        
        result = await market_data_service.validate_market_data(invalid_price)
        
        assert result.is_valid is False
        assert result.quality_score < 0.8
        assert "Invalid price values" in " ".join(result.issues)
    
    @pytest.mark.asyncio
    async def test_validate_market_data_missing_fields(self, market_data_service):
        """Test validation of market data with missing required fields."""
        incomplete_price = MarketPrice(
            commodity="",  # Missing commodity
            market="",     # Missing market
            state="Delhi",
            min_price=Decimal("20.00"),
            max_price=Decimal("30.00"),
            modal_price=Decimal("25.00"),
            unit=PriceUnit.PER_KG,
            date=date.today(),
            source=DataSource.AGMARKNET
        )
        
        result = await market_data_service.validate_market_data(incomplete_price)
        
        assert result.is_valid is False
        assert "Commodity name is missing" in " ".join(result.issues)
        assert "Market name is missing" in " ".join(result.issues)
    
    @pytest.mark.asyncio
    async def test_validate_market_data_unreasonable_prices(self, market_data_service):
        """Test validation of market data with unreasonable price ranges."""
        unreasonable_price = MarketPrice(
            commodity="onion",
            market="Delhi",
            state="Delhi",
            min_price=Decimal("1.00"),
            max_price=Decimal("100.00"),  # 100x difference (unreasonable)
            modal_price=Decimal("50.00"),
            unit=PriceUnit.PER_KG,
            date=date.today(),
            source=DataSource.AGMARKNET
        )
        
        result = await market_data_service.validate_market_data(unreasonable_price)
        
        assert "unreasonable" in " ".join(result.issues).lower()
        assert "Verify price data accuracy" in " ".join(result.recommendations)
    
    @pytest.mark.asyncio
    async def test_validate_market_data_future_date(self, market_data_service):
        """Test validation of 