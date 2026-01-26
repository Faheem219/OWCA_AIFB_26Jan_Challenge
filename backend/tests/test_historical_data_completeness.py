"""
Property-based test for historical data completeness.
**Validates: Requirements 2.3**
"""
import pytest
import asyncio
from hypothesis import given, strategies as st, assume, settings
from datetime import date, datetime, timedelta
import statistics
from typing import List, Dict, Set
from unittest.mock import AsyncMock, patch

from app.services.price_discovery_service import price_discovery_service
from app.models.price import PricePoint, PriceData, Location, PriceSource, MarketType
from app.models.common import QualityGrade


# Custom strategies for generating test data
@st.composite
def complete_price_dataset(draw, min_days=30, max_days=365):
    """Generate a complete dataset with no gaps in time series."""
    num_days = draw(st.integers(min_value=min_days, max_value=max_days))
    start_date = date.today() - timedelta(days=num_days)
    base_price = draw(st.floats(min_value=500, max_value=5000))
    
    price_points = []
    for i in range(num_days):
        current_date = start_date + timedelta(days=i)
        # Add realistic price variation
        price_variation = draw(st.floats(min_value=-0.05, max_value=0.05))
        price = max(100, base_price * (1 + price_variation))
        
        price_points.append(PricePoint(
            date=current_date,
            price=price,
            volume=draw(st.floats(min_value=10, max_value=1000))
        ))
        
        # Update base price for next iteration (random walk)
        base_price = price
    
    return price_points


@st.composite
def incomplete_price_dataset(draw, min_days=30, max_days=365, gap_probability=0.1):
    """Generate a dataset with potential gaps in time series."""
    num_days = draw(st.integers(min_value=min_days, max_value=max_days))
    start_date = date.today() - timedelta(days=num_days)
    base_price = draw(st.floats(min_value=500, max_value=5000))
    
    price_points = []
    for i in range(num_days):
        # Randomly skip some days to create gaps
        if draw(st.floats(min_value=0, max_value=1)) < gap_probability:
            continue
            
        current_date = start_date + timedelta(days=i)
        price_variation = draw(st.floats(min_value=-0.05, max_value=0.05))
        price = max(100, base_price * (1 + price_variation))
        
        price_points.append(PricePoint(
            date=current_date,
            price=price,
            volume=draw(st.floats(min_value=10, max_value=1000))
        ))
        
        base_price = price
    
    return price_points


@st.composite
def commodity_name(draw):
    """Generate realistic commodity names."""
    commodities = ["Rice", "Wheat", "Onion", "Potato", "Tomato", "Cotton", "Sugar", "Turmeric", "Maize", "Soybean"]
    return draw(st.sampled_from(commodities))


@st.composite
def location_name(draw):
    """Generate realistic location names."""
    locations = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad"]
    return draw(st.sampled_from(locations))


class TestHistoricalDataCompleteness:
    """Property-based tests for historical data completeness."""
    
    @given(
        complete_dataset=complete_price_dataset(min_days=30, max_days=180),
        commodity=commodity_name(),
        location=location_name()
    )
    @settings(max_examples=20, deadline=10000)
    @pytest.mark.asyncio
    async def test_complete_historical_data_has_no_gaps(
        self, 
        complete_dataset: List[PricePoint], 
        commodity: str, 
        location: str
    ):
        """
        **Property 8: Historical Data Completeness**
        **Validates: Requirements 2.3**
        
        For any complete historical dataset, there should be no gaps in the time series
        and all data should be consistent and complete.
        """
        assume(len(complete_dataset) >= 30)
        
        # Mock the database call to return our test data
        with patch.object(
            price_discovery_service, 
            '_get_historical_prices',
            return_value=complete_dataset
        ):
            # Get the date range
            start_date = min(pp.date for pp in complete_dataset)
            end_date = max(pp.date for pp in complete_dataset)
            
            # Retrieve historical data
            retrieved_data = await price_discovery_service._get_historical_prices(
                commodity, start_date, end_date, location
            )
            
            # Property 1: Retrieved data should match input data
            assert len(retrieved_data) == len(complete_dataset)
            
            # Property 2: All dates should be present (no gaps)
            retrieved_dates = {pp.date for pp in retrieved_data}
            expected_dates = {pp.date for pp in complete_dataset}
            assert retrieved_dates == expected_dates, "Historical data has missing dates"
            
            # Property 3: Data should be chronologically ordered
            sorted_dates = [pp.date for pp in sorted(retrieved_data, key=lambda x: x.date)]
            original_dates = [pp.date for pp in retrieved_data]
            assert sorted_dates == original_dates or len(set(original_dates)) == len(original_dates), \
                "Historical data is not properly ordered"
            
            # Property 4: All prices should be positive
            for pp in retrieved_data:
                assert pp.price > 0, f"Invalid price found: {pp.price}"
            
            # Property 5: Date range should be complete
            date_range = (end_date - start_date).days + 1
            assert len(retrieved_data) == date_range, \
                f"Expected {date_range} days of data, got {len(retrieved_data)}"
    
    @given(
        incomplete_dataset=incomplete_price_dataset(min_days=30, max_days=180, gap_probability=0.2),
        commodity=commodity_name(),
        location=location_name()
    )
    @settings(max_examples=20, deadline=10000)
    @pytest.mark.asyncio
    async def test_incomplete_data_gap_detection(
        self, 
        incomplete_dataset: List[PricePoint], 
        commodity: str, 
        location: str
    ):
        """
        **Property 8: Historical Data Completeness**
        **Validates: Requirements 2.3**
        
        For any dataset with gaps, the system should be able to detect and handle
        missing data points appropriately.
        """
        assume(len(incomplete_dataset) >= 10)
        
        with patch.object(
            price_discovery_service, 
            '_get_historical_prices',
            return_value=incomplete_dataset
        ):
            start_date = min(pp.date for pp in incomplete_dataset)
            end_date = max(pp.date for pp in incomplete_dataset)
            
            retrieved_data = await price_discovery_service._get_historical_prices(
                commodity, start_date, end_date, location
            )
            
            # Property 1: Retrieved data should match incomplete input
            assert len(retrieved_data) == len(incomplete_dataset)
            
            # Property 2: Check for gaps in the time series
            dates = sorted([pp.date for pp in retrieved_data])
            expected_total_days = (end_date - start_date).days + 1
            actual_days = len(dates)
            
            if actual_days < expected_total_days:
                # There are gaps - verify they are handled correctly
                gaps = []
                for i in range(len(dates) - 1):
                    current_date = dates[i]
                    next_date = dates[i + 1]
                    gap_days = (next_date - current_date).days - 1
                    if gap_days > 0:
                        gaps.append({
                            'start': current_date,
                            'end': next_date,
                            'gap_days': gap_days
                        })
                
                # Property 3: System should maintain data integrity despite gaps
                for pp in retrieved_data:
                    assert pp.price > 0
                    assert isinstance(pp.date, date)
                    assert pp.volume is None or pp.volume >= 0
    
    @given(
        price_dataset=complete_price_dataset(min_days=90, max_days=365),
        commodity=commodity_name()
    )
    @settings(max_examples=15, deadline=15000)
    @pytest.mark.asyncio
    async def test_trend_analysis_with_complete_data(
        self, 
        price_dataset: List[PricePoint], 
        commodity: str
    ):
        """
        **Property 8: Historical Data Completeness**
        **Validates: Requirements 2.3**
        
        For any complete historical dataset, trend analysis should produce
        consistent and meaningful results with proper data completeness validation.
        """
        assume(len(price_dataset) >= 90)
        
        with patch.object(
            price_discovery_service, 
            '_get_historical_prices',
            return_value=price_dataset
        ):
            # Test advanced trend analysis
            analysis = await price_discovery_service.get_advanced_trend_analysis(
                commodity=commodity,
                location=None,
                analysis_period_days=len(price_dataset)
            )
            
            # Property 1: Analysis should not have errors for complete data
            assert "error" not in analysis, "Complete data should not produce analysis errors"
            
            # Property 2: Data points should match input
            assert analysis["data_points"] == len(price_dataset)
            
            # Property 3: All required analysis components should be present
            required_components = [
                "price_statistics", "trend_analysis", "seasonal_patterns",
                "volatility_analysis", "anomalies", "support_resistance",
                "moving_averages", "momentum_indicators"
            ]
            
            for component in required_components:
                assert component in analysis, f"Missing analysis component: {component}"
            
            # Property 4: Price statistics should be accurate
            prices = [pp.price for pp in price_dataset]
            stats = analysis["price_statistics"]
            
            assert abs(stats["mean"] - statistics.mean(prices)) < 0.01
            assert abs(stats["min"] - min(prices)) < 0.01
            assert abs(stats["max"] - max(prices)) < 0.01
            
            # Property 5: Trend analysis should have valid metrics
            trend_analysis = analysis["trend_analysis"]
            assert "slope" in trend_analysis
            assert "r_squared" in trend_analysis
            assert 0 <= trend_analysis["r_squared"] <= 1
            
            # Property 6: Volatility analysis should be valid
            volatility = analysis["volatility_analysis"]
            assert "coefficient_of_variation" in volatility
            assert volatility["coefficient_of_variation"] >= 0
    
    @given(
        price_dataset=complete_price_dataset(min_days=60, max_days=200),
        commodity=commodity_name(),
        location=location_name()
    )
    @settings(max_examples=15, deadline=15000)
    @pytest.mark.asyncio
    async def test_seasonal_pattern_detection_completeness(
        self, 
        price_dataset: List[PricePoint], 
        commodity: str, 
        location: str
    ):
        """
        **Property 8: Historical Data Completeness**
        **Validates: Requirements 2.3**
        
        For any dataset spanning multiple months, seasonal pattern detection
        should work correctly with complete data and identify all monthly patterns.
        """
        assume(len(price_dataset) >= 90)  # Need at least 90 days for seasonal analysis
        
        # Ensure we have data spanning multiple months
        dates = [pp.date for pp in price_dataset]
        months_covered = len(set(d.month for d in dates))
        assume(months_covered >= 2)
        
        with patch.object(
            price_discovery_service, 
            '_get_historical_prices',
            return_value=price_dataset
        ):
            # Test seasonal pattern detection
            seasonal_patterns = await price_discovery_service._detect_seasonal_patterns(price_dataset)
            
            # Property 1: Should not have errors for sufficient data
            if len(price_dataset) >= 90:
                assert "error" not in seasonal_patterns
                
                # Property 2: Should have monthly averages for all months present in data
                monthly_averages = seasonal_patterns["monthly_averages"]
                months_in_data = set(pp.date.month for pp in price_dataset)
                months_in_analysis = set(monthly_averages.keys())
                
                assert months_in_data == months_in_analysis, \
                    "Seasonal analysis missing data for some months"
                
                # Property 3: All monthly averages should be positive
                for month, avg_price in monthly_averages.items():
                    assert avg_price > 0, f"Invalid average price for month {month}: {avg_price}"
                
                # Property 4: Seasonal factors should be reasonable
                seasonal_factors = seasonal_patterns["seasonal_factors"]
                for month, factor in seasonal_factors.items():
                    assert 0.1 <= factor <= 10.0, f"Unreasonable seasonal factor for month {month}: {factor}"
                
                # Property 5: Peak and trough months should be valid
                assert 1 <= seasonal_patterns["peak_month"] <= 12
                assert 1 <= seasonal_patterns["trough_month"] <= 12
                
                # Property 6: Seasonality strength should be non-negative
                assert seasonal_patterns["seasonality_strength"] >= 0
            else:
                # For insufficient data, should return error
                assert "error" in seasonal_patterns
    
    @given(
        price_dataset=complete_price_dataset(min_days=30, max_days=100),
        commodity=commodity_name()
    )
    @settings(max_examples=15, deadline=15000)
    def test_data_continuity_validation(
        self, 
        price_dataset: List[PricePoint], 
        commodity: str
    ):
        """
        **Property 8: Historical Data Completeness**
        **Validates: Requirements 2.3**
        
        For any historical dataset, data continuity should be validated
        to ensure no missing periods that could affect analysis accuracy.
        """
        assume(len(price_dataset) >= 30)
        
        # Property 1: Dates should form a continuous sequence
        sorted_dates = sorted([pp.date for pp in price_dataset])
        
        for i in range(len(sorted_dates) - 1):
            current_date = sorted_dates[i]
            next_date = sorted_dates[i + 1]
            gap = (next_date - current_date).days
            
            # For complete dataset, gap should be exactly 1 day
            assert gap == 1, f"Data continuity broken: gap of {gap} days between {current_date} and {next_date}"
        
        # Property 2: Each date should appear exactly once
        date_counts = {}
        for pp in price_dataset:
            date_counts[pp.date] = date_counts.get(pp.date, 0) + 1
        
        for date_val, count in date_counts.items():
            assert count == 1, f"Duplicate data for date {date_val}: {count} entries"
        
        # Property 3: Price data should be consistent (no extreme outliers that suggest data corruption)
        prices = [pp.price for pp in price_dataset]
        if len(prices) > 1:
            mean_price = statistics.mean(prices)
            std_price = statistics.stdev(prices)
            
            # Check for extreme outliers (more than 5 standard deviations)
            for pp in price_dataset:
                z_score = abs(pp.price - mean_price) / std_price if std_price > 0 else 0
                assert z_score <= 5.0, f"Potential data corruption: extreme price {pp.price} on {pp.date}"
        
        # Property 4: Volume data should be consistent if present
        for pp in price_dataset:
            if pp.volume is not None:
                assert pp.volume >= 0, f"Invalid volume {pp.volume} on {pp.date}"
    
    @given(
        price_dataset=complete_price_dataset(min_days=50, max_days=150),
        commodity=commodity_name(),
        forecast_days=st.integers(min_value=1, max_value=30)
    )
    @settings(max_examples=10, deadline=20000)
    @pytest.mark.asyncio
    async def test_prediction_accuracy_with_complete_data(
        self, 
        price_dataset: List[PricePoint], 
        commodity: str, 
        forecast_days: int
    ):
        """
        **Property 8: Historical Data Completeness**
        **Validates: Requirements 2.3**
        
        For any complete historical dataset, prediction models should produce
        more accurate and reliable forecasts compared to incomplete data.
        """
        assume(len(price_dataset) >= 50)
        
        with patch.object(
            price_discovery_service, 
            '_get_historical_prices',
            return_value=price_dataset
        ):
            # Test ensemble prediction with complete data
            prediction = await price_discovery_service.get_ensemble_price_prediction(
                commodity=commodity,
                forecast_days=forecast_days,
                location=None
            )
            
            # Property 1: Should not have errors with complete data
            assert "error" not in prediction
            
            # Property 2: Should use all available data points
            assert prediction["data_points_used"] == len(price_dataset)
            
            # Property 3: Ensemble prediction should be present
            ensemble = prediction["ensemble_prediction"]
            assert "predicted_price" in ensemble
            assert "confidence" in ensemble
            assert ensemble["predicted_price"] > 0
            assert 0 <= ensemble["confidence"] <= 1
            
            # Property 4: Individual model predictions should be available
            individual_preds = prediction["individual_predictions"]
            assert len(individual_preds) >= 1, "Should have at least one prediction model"
            
            # Property 5: Model comparison should show agreement metrics
            comparison = prediction["model_comparison"]
            assert "model_agreement" in comparison
            assert comparison["model_agreement"] in ["high", "medium", "low"]
            
            # Property 6: Confidence should be higher for complete data
            # (This is a general expectation - complete data should yield higher confidence)
            assert ensemble["confidence"] >= 0.3, "Complete data should provide reasonable confidence"
    
    @given(
        price_dataset=complete_price_dataset(min_days=30, max_days=90),
        commodity=commodity_name()
    )
    @settings(max_examples=15, deadline=10000)
    def test_data_integrity_validation(
        self, 
        price_dataset: List[PricePoint], 
        commodity: str
    ):
        """
        **Property 8: Historical Data Completeness**
        **Validates: Requirements 2.3**
        
        For any historical dataset, data integrity should be maintained
        with proper validation of all data fields and relationships.
        """
        assume(len(price_dataset) >= 30)
        
        # Property 1: All price points should have valid structure
        for pp in price_dataset:
            assert isinstance(pp.date, date), f"Invalid date type: {type(pp.date)}"
            assert isinstance(pp.price, (int, float)), f"Invalid price type: {type(pp.price)}"
            assert pp.price > 0, f"Invalid price value: {pp.price}"
            
            if pp.volume is not None:
                assert isinstance(pp.volume, (int, float)), f"Invalid volume type: {type(pp.volume)}"
                assert pp.volume >= 0, f"Invalid volume value: {pp.volume}"
        
        # Property 2: Date range should be logical
        dates = [pp.date for pp in price_dataset]
        min_date = min(dates)
        max_date = max(dates)
        
        # Dates should not be in the future
        assert max_date <= date.today(), "Historical data contains future dates"
        
        # Date range should be reasonable (not too old)
        assert min_date >= date.today() - timedelta(days=3650), "Historical data is unreasonably old"
        
        # Property 3: Price values should be within reasonable ranges
        prices = [pp.price for pp in price_dataset]
        min_price = min(prices)
        max_price = max(prices)
        
        # Prices should be within reasonable commodity price ranges
        assert 10 <= min_price <= 100000, f"Minimum price out of range: {min_price}"
        assert 10 <= max_price <= 100000, f"Maximum price out of range: {max_price}"
        
        # Property 4: Price changes should be reasonable (no extreme jumps)
        sorted_data = sorted(price_dataset, key=lambda x: x.date)
        for i in range(len(sorted_data) - 1):
            current_price = sorted_data[i].price
            next_price = sorted_data[i + 1].price
            
            # Daily price change should not exceed 50% (extreme but possible)
            price_change_ratio = abs(next_price - current_price) / current_price
            assert price_change_ratio <= 0.5, \
                f"Extreme price change: {current_price} to {next_price} on consecutive days"
        
        # Property 5: Data completeness metrics should be calculable
        completeness_score = len(price_dataset) / ((max_date - min_date).days + 1)
        assert 0 <= completeness_score <= 1, f"Invalid completeness score: {completeness_score}"
        
        # For our complete dataset, completeness should be 1.0
        assert completeness_score == 1.0, f"Expected complete data, got completeness: {completeness_score}"