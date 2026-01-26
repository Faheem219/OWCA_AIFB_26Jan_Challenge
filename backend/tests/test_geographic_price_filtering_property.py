"""
Property-based test for geographic price filtering accuracy.

**Task Details:**
- **Property 9: Geographic Price Filtering Accuracy**
- **Validates: Requirements 2.5**

This test validates that the system provides location-based price variations 
with accurate radius-based filtering for finding markets within specified distances.
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import date, datetime, timedelta
from typing import List, Optional
import math
import statistics

from app.services.price_discovery_service import price_discovery_service
from app.models.price import (
    Location, PriceData, QualityGrade, MarketType, PriceSource,
    GeographicPriceQuery, GeographicPriceResult, RadiusFilterResult
)
from app.data.sample_location_data import SAMPLE_LOCATIONS


# Custom strategies for geographic testing
@st.composite
def location_with_coordinates_strategy(draw):
    """Generate Location objects with valid coordinates."""
    # Use realistic Indian coordinates
    latitude = draw(st.floats(min_value=8.0, max_value=37.0))  # India's lat range
    longitude = draw(st.floats(min_value=68.0, max_value=97.0))  # India's lon range
    
    return Location(
        state=draw(st.sampled_from([
            "Maharashtra", "Punjab", "Uttar Pradesh", "Karnataka", 
            "Tamil Nadu", "Gujarat", "Rajasthan", "West Bengal"
        ])),
        district=draw(st.text(min_size=3, max_size=15, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll'), min_codepoint=65, max_codepoint=122
        ))),
        market_name=draw(st.text(min_size=5, max_size=25, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=65, max_codepoint=122
        ))) + " Market",
        latitude=latitude,
        longitude=longitude,
        pincode=draw(st.text(min_size=6, max_size=6, alphabet=st.characters(
            whitelist_categories=('Nd',)
        )))
    )


@st.composite
def commodity_strategy(draw):
    """Generate valid commodity names."""
    return draw(st.sampled_from([
        'Rice', 'Wheat', 'Onion', 'Potato', 'Tomato', 'Cotton', 'Sugar'
    ]))


@st.composite
def radius_strategy(draw):
    """Generate valid radius values."""
    return draw(st.integers(min_value=10, max_value=200))


class TestGeographicPriceFilteringProperty:
    """Property-based test for geographic price filtering accuracy."""
    
    @given(
        commodity=commodity_strategy(),
        center_location=location_with_coordinates_strategy(),
        radius_km=radius_strategy()
    )
    @settings(max_examples=15, deadline=10000)  # 5-20 examples for faster execution
    @pytest.mark.asyncio
    async def test_property_9_geographic_price_filtering_accuracy(
        self, 
        commodity: str, 
        center_location: Location, 
        radius_km: int
    ):
        """
        **Validates: Requirements 2.5**
        Property 9: Geographic Price Filtering Accuracy
        
        For any location-based price search, all returned results should be 
        within the specified radius (default 50km) of the query location.
        
        This property validates:
        1. Distance calculations are accurate using Haversine formula
        2. All returned markets are within the specified radius
        3. Location-based filtering works correctly
        4. Radius accuracy is maintained across different locations and radii
        """
        assume(center_location.latitude is not None)
        assume(center_location.longitude is not None)
        assume(-90 <= center_location.latitude <= 90)
        assume(-180 <= center_location.longitude <= 180)
        assume(radius_km > 0)
        
        try:
            # Execute geographic price filtering
            result = await price_discovery_service.get_prices_within_radius(
                commodity=commodity,
                center_location=center_location,
                radius_km=radius_km,
                include_msp_comparison=False  # Simplify for property testing
            )
            
            # Property 1: All results must be RadiusFilterResult type
            assert isinstance(result, RadiusFilterResult), \
                f"Expected RadiusFilterResult, got {type(result)}"
            
            # Property 2: Query parameters should match input
            assert result.query.commodity == commodity, \
                f"Query commodity mismatch: expected {commodity}, got {result.query.commodity}"
            assert result.query.radius_km == radius_km, \
                f"Query radius mismatch: expected {radius_km}, got {result.query.radius_km}"
            
            # Property 3: All results with distance data must be within radius
            for price_result in result.results:
                assert isinstance(price_result, GeographicPriceResult), \
                    f"Expected GeographicPriceResult, got {type(price_result)}"
                
                # If distance is calculated, it must be within radius
                if price_result.distance_km is not None:
                    assert price_result.distance_km <= radius_km, \
                        f"Market {price_result.price_data.market_name} at distance " \
                        f"{price_result.distance_km}km exceeds radius {radius_km}km"
                    
                    # Verify distance calculation accuracy using Haversine formula
                    if (price_result.price_data.location.latitude is not None and 
                        price_result.price_data.location.longitude is not None):
                        
                        calculated_distance = self._calculate_haversine_distance(
                            center_location.latitude, center_location.longitude,
                            price_result.price_data.location.latitude,
                            price_result.price_data.location.longitude
                        )
                        
                        # Allow small tolerance for floating point precision
                        distance_tolerance = 0.1  # 100 meters tolerance
                        assert abs(price_result.distance_km - calculated_distance) <= distance_tolerance, \
                            f"Distance calculation error: expected {calculated_distance:.3f}km, " \
                            f"got {price_result.distance_km:.3f}km (tolerance: {distance_tolerance}km)"
            
            # Property 4: Statistics should be consistent with results
            if result.results:
                prices = [r.price_data.price_modal for r in result.results]
                
                if result.average_price is not None:
                    expected_avg = statistics.mean(prices)
                    # Allow small tolerance for floating point precision
                    assert abs(result.average_price - expected_avg) < 0.01, \
                        f"Average price calculation error: expected {expected_avg:.2f}, " \
                        f"got {result.average_price:.2f}"
                
                if result.price_statistics:
                    if 'min' in result.price_statistics:
                        assert result.price_statistics['min'] == min(prices), \
                            f"Min price mismatch: expected {min(prices)}, " \
                            f"got {result.price_statistics['min']}"
                    
                    if 'max' in result.price_statistics:
                        assert result.price_statistics['max'] == max(prices), \
                            f"Max price mismatch: expected {max(prices)}, " \
                            f"got {result.price_statistics['max']}"
            
            # Property 5: Total markets count should match results length
            assert result.total_markets == len(result.results), \
                f"Total markets count mismatch: expected {len(result.results)}, " \
                f"got {result.total_markets}"
            
            # Property 6: Distance statistics should be consistent
            if result.distance_statistics:
                distances = [r.distance_km for r in result.results if r.distance_km is not None]
                
                if distances and 'min' in result.distance_statistics:
                    assert result.distance_statistics['min'] == min(distances), \
                        f"Min distance mismatch: expected {min(distances)}, " \
                        f"got {result.distance_statistics['min']}"
                
                if distances and 'max' in result.distance_statistics:
                    assert result.distance_statistics['max'] == max(distances), \
                        f"Max distance mismatch: expected {max(distances)}, " \
                        f"got {result.distance_statistics['max']}"
                    
                    # Max distance should not exceed radius
                    assert result.distance_statistics['max'] <= radius_km, \
                        f"Max distance {result.distance_statistics['max']}km exceeds " \
                        f"radius {radius_km}km"
            
            # Property 7: Quality distribution should sum to total results
            if result.quality_distribution:
                total_quality_count = sum(result.quality_distribution.values())
                assert total_quality_count == len(result.results), \
                    f"Quality distribution sum {total_quality_count} doesn't match " \
                    f"results count {len(result.results)}"
            
        except Exception as e:
            # Log the error for debugging but allow some service failures
            # in property testing due to external dependencies
            if "insufficient data" in str(e).lower() or "no data" in str(e).lower():
                # This is acceptable - no data available for this combination
                assume(False)  # Skip this test case
            else:
                # Re-raise unexpected errors
                raise e
    
    def _calculate_haversine_distance(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Args:
            lat1, lon1: Latitude and longitude of first point
            lat2, lon2: Latitude and longitude of second point
            
        Returns:
            Distance in kilometers
        """
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        earth_radius = 6371.0
        
        return earth_radius * c
    
    @given(
        commodity=commodity_strategy(),
        radius_km=radius_strategy()
    )
    @settings(max_examples=10, deadline=8000)
    @pytest.mark.asyncio
    async def test_geographic_filtering_with_sample_locations(
        self, 
        commodity: str, 
        radius_km: int
    ):
        """
        Test geographic filtering using known sample locations with verified coordinates.
        
        This test uses the predefined SAMPLE_LOCATIONS to ensure we have valid
        coordinate data for testing distance calculations.
        """
        assume(len(SAMPLE_LOCATIONS) > 0)
        
        # Use first sample location as center
        center_location = SAMPLE_LOCATIONS[0]
        
        try:
            result = await price_discovery_service.get_prices_within_radius(
                commodity=commodity,
                center_location=center_location,
                radius_km=radius_km,
                include_msp_comparison=False
            )
            
            # Verify all distance calculations are within radius
            for price_result in result.results:
                if price_result.distance_km is not None:
                    assert price_result.distance_km <= radius_km, \
                        f"Distance {price_result.distance_km}km exceeds radius {radius_km}km"
                    
                    # Verify distance is non-negative
                    assert price_result.distance_km >= 0, \
                        f"Distance cannot be negative: {price_result.distance_km}km"
            
            # Verify result consistency
            assert result.total_markets == len(result.results)
            
            # If we have results, verify statistics are reasonable
            if result.results and result.average_price is not None:
                prices = [r.price_data.price_modal for r in result.results]
                assert min(prices) <= result.average_price <= max(prices), \
                    f"Average price {result.average_price} outside range [{min(prices)}, {max(prices)}]"
        
        except Exception as e:
            if "insufficient data" in str(e).lower():
                assume(False)  # Skip if no data available
            else:
                raise e


if __name__ == "__main__":
    """
    Run the property-based test directly for development and debugging.
    """
    import asyncio
    
    async def run_test():
        test_instance = TestGeographicPriceFilteringProperty()
        
        # Test with a known location
        mumbai_location = Location(
            state="Maharashtra",
            district="Mumbai", 
            market_name="Vashi APMC Market",
            latitude=19.0760,
            longitude=73.0777,
            pincode="400703"
        )
        
        print("🧪 Running Geographic Price Filtering Property Test")
        print("=" * 60)
        
        try:
            await test_instance.test_property_9_geographic_price_filtering_accuracy(
                commodity="Rice",
                center_location=mumbai_location,
                radius_km=100
            )
            print("✅ Property test passed!")
            
        except Exception as e:
            print(f"❌ Property test failed: {str(e)}")
            raise
    
    asyncio.run(run_test())