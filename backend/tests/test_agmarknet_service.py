"""
Tests for AGMARKNET service integration.
"""
import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, patch

from app.services.agmarknet_service import AGMARKNETService, agmarknet_service
from app.models.price import PriceData, Location, PriceSource, MarketType, QualityGrade


class TestAGMARKNETService:
    """Test cases for AGMARKNET service."""
    
    @pytest.fixture
    def service(self):
        """Create AGMARKNET service instance."""
        return AGMARKNETService()
    
    @pytest.fixture
    def sample_agmarknet_response(self):
        """Sample AGMARKNET API response."""
        return {
            "records": [
                {
                    "state": "Maharashtra",
                    "district": "Mumbai",
                    "market": "APMC Market",
                    "commodity": "Rice",
                    "variety": "Basmati",
                    "arrival_date": "01/01/2024",
                    "min_price": "2000",
                    "max_price": "2200",
                    "modal_price": "2100",
                    "units": "Quintal",
                    "arrivals": "150"
                },
                {
                    "state": "Punjab",
                    "district": "Ludhiana",
                    "market": "Grain Market",
                    "commodity": "Wheat",
                    "variety": "Sharbati",
                    "arrival_date": "01/01/2024",
                    "min_price": "2300",
                    "max_price": "2500",
                    "modal_price": "2400",
                    "units": "Quintal",
                    "arrivals": "200"
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_parse_agmarknet_response(self, service, sample_agmarknet_response):
        """Test parsing AGMARKNET API response."""
        price_data_list = await service._parse_agmarknet_response(sample_agmarknet_response)
        
        assert len(price_data_list) == 2
        
        # Test first record (Rice)
        rice_data = price_data_list[0]
        assert rice_data.commodity == "Rice"
        assert rice_data.variety == "Basmati"
        assert rice_data.location.state == "Maharashtra"
        assert rice_data.location.district == "Mumbai"
        assert rice_data.location.market_name == "APMC Market"
        assert rice_data.price_min == 2000.0
        assert rice_data.price_max == 2200.0
        assert rice_data.price_modal == 2100.0
        assert rice_data.unit == "Quintal"
        assert rice_data.source == PriceSource.AGMARKNET
        assert rice_data.arrivals == 150.0
        
        # Test second record (Wheat)
        wheat_data = price_data_list[1]
        assert wheat_data.commodity == "Wheat"
        assert wheat_data.variety == "Sharbati"
        assert wheat_data.location.state == "Punjab"
        assert wheat_data.price_modal == 2400.0
    
    def test_parse_price(self, service):
        """Test price parsing from various formats."""
        assert service._parse_price("2000") == 2000.0
        assert service._parse_price("₹2,500") == 2500.0
        assert service._parse_price("NR") == 0.0
        assert service._parse_price("") == 0.0
        assert service._parse_price(None) == 0.0
        assert service._parse_price("invalid") == 0.0
    
    def test_parse_date(self, service):
        """Test date parsing from various formats."""
        assert service._parse_date("01/01/2024") == date(2024, 1, 1)
        assert service._parse_date("2024-01-01") == date(2024, 1, 1)
        assert service._parse_date("01-01-2024") == date(2024, 1, 1)
        assert service._parse_date("") is None
        assert service._parse_date("invalid") is None
    
    def test_parse_arrivals(self, service):
        """Test arrivals parsing."""
        assert service._parse_arrivals("150") == 150.0
        assert service._parse_arrivals("1,500") == 1500.0
        assert service._parse_arrivals("NR") is None
        assert service._parse_arrivals("") is None
        assert service._parse_arrivals("invalid") is None
    
    def test_determine_quality_grade(self, service):
        """Test quality grade determination."""
        # Premium quality (modal closer to max)
        assert service._determine_quality_grade(2000, 2200, 2180) == QualityGrade.PREMIUM
        
        # Below standard (modal closer to min)
        assert service._determine_quality_grade(2000, 2200, 2020) == QualityGrade.BELOW_STANDARD
        
        # Standard quality (modal in middle)
        assert service._determine_quality_grade(2000, 2200, 2100) == QualityGrade.STANDARD
        
        # All same price
        assert service._determine_quality_grade(2000, 2000, 2000) == QualityGrade.STANDARD
    
    @pytest.mark.asyncio
    async def test_get_mock_data(self, service):
        """Test mock data generation."""
        mock_data = await service._get_mock_data(commodity="Rice", state="Maharashtra")
        
        assert len(mock_data) == 1
        assert mock_data[0].commodity == "Rice"
        assert mock_data[0].location.state == "Maharashtra"
        assert mock_data[0].source == PriceSource.AGMARKNET
        assert mock_data[0].price_modal > 0
    
    @pytest.mark.asyncio
    async def test_get_mock_data_multiple_commodities(self, service):
        """Test mock data generation for multiple commodities."""
        mock_data = await service._get_mock_data()
        
        assert len(mock_data) == 5  # Default limit
        commodities = {pd.commodity for pd in mock_data}
        assert "Rice" in commodities
        assert "Wheat" in commodities
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_fetch_daily_rates_success(self, mock_client_class, service, sample_agmarknet_response):
        """Test successful AGMARKNET API call."""
        # Mock the async client and response
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = sample_agmarknet_response
        mock_response.raise_for_status.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None
        
        # Set API key for test
        service.api_key = "test_api_key"
        
        price_data = await service.fetch_daily_rates(commodity="Rice")
        
        assert len(price_data) == 2
        assert price_data[0].commodity == "Rice"
        assert price_data[1].commodity == "Wheat"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_fetch_daily_rates_api_error(self, mock_client_class, service):
        """Test AGMARKNET API error handling."""
        # Mock API error
        mock_client_class.side_effect = Exception("API Error")
        
        # Set API key for test
        service.api_key = "test_api_key"
        
        # Should fallback to cached/mock data
        price_data = await service.fetch_daily_rates(commodity="Rice")
        
        # Should return mock data as fallback
        assert len(price_data) >= 1
        assert price_data[0].source == PriceSource.AGMARKNET
    
    @pytest.mark.asyncio
    async def test_fetch_daily_rates_no_api_key(self, service):
        """Test behavior when no API key is configured."""
        # Ensure no API key
        service.api_key = None
        
        price_data = await service.fetch_daily_rates(commodity="Rice")
        
        # Should return mock data
        assert len(price_data) >= 1
        assert price_data[0].commodity == "Rice"
        assert price_data[0].source == PriceSource.AGMARKNET
    
    @pytest.mark.asyncio
    async def test_commodity_mappings(self, service):
        """Test commodity name mappings."""
        assert "Rice" in service.commodity_mappings["rice"]
        assert "Wheat" in service.commodity_mappings["wheat"]
        assert "Onion" in service.commodity_mappings["onion"]
        
        # Test case insensitive mapping
        agmarknet_commodities = service.commodity_mappings.get("rice", ["rice"])
        assert len(agmarknet_commodities) > 0
    
    @pytest.mark.asyncio
    @patch('app.services.agmarknet_service.get_database')
    async def test_store_price_data(self, mock_get_db, service):
        """Test storing price data in database."""
        # Mock database
        mock_collection = AsyncMock()
        mock_db = AsyncMock()
        mock_db.price_data = mock_collection
        mock_get_db.return_value = mock_db
        
        # Mock upsert result
        mock_result = AsyncMock()
        mock_result.upserted_id = "test_id"
        mock_result.modified_count = 0
        mock_collection.replace_one.return_value = mock_result
        
        # Create test data
        test_data = [
            PriceData(
                commodity="Rice",
                market_name="Test Market",
                location=Location(
                    state="Test State",
                    district="Test District",
                    market_name="Test Market"
                ),
                price_min=2000.0,
                price_max=2200.0,
                price_modal=2100.0,
                quality_grade=QualityGrade.STANDARD,
                unit="Quintal",
                date=date.today(),
                source=PriceSource.AGMARKNET,
                market_type=MarketType.MANDI
            )
        ]
        
        stored_count = await service.store_price_data(test_data)
        
        assert stored_count == 1
        mock_collection.replace_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_empty_price_data(self, service):
        """Test storing empty price data list."""
        stored_count = await service.store_price_data([])
        assert stored_count == 0
    
    @pytest.mark.asyncio
    @patch('app.services.agmarknet_service.get_database')
    async def test_get_prices_from_db(self, mock_get_db, service):
        """Test getting prices from database."""
        # Mock database
        mock_collection = AsyncMock()
        mock_db = AsyncMock()
        mock_db.price_data = mock_collection
        mock_get_db.return_value = mock_db
        
        # Mock database response
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = [
            {
                "commodity": "Rice",
                "market_name": "Test Market",
                "location": {
                    "state": "Test State",
                    "district": "Test District",
                    "market_name": "Test Market"
                },
                "price_min": 2000.0,
                "price_max": 2200.0,
                "price_modal": 2100.0,
                "quality_grade": "standard",
                "unit": "Quintal",
                "date": date.today().isoformat(),
                "source": "agmarknet",
                "market_type": "mandi",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        mock_collection.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        prices = await service._get_prices_from_db("Rice", "Test State", 50)
        
        assert len(prices) == 1
        assert prices[0].commodity == "Rice"
        assert prices[0].location.state == "Test State"


@pytest.mark.asyncio
async def test_global_service_instance():
    """Test that global service instance is properly configured."""
    assert agmarknet_service is not None
    assert isinstance(agmarknet_service, AGMARKNETService)
    assert agmarknet_service.base_url is not None
    assert agmarknet_service.timeout > 0
    assert agmarknet_service.max_retries > 0