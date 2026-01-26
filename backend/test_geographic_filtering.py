#!/usr/bin/env python3
"""
Test script for geographic price filtering functionality.
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.price_discovery_service import price_discovery_service
from app.data.sample_location_data import SAMPLE_LOCATIONS, populate_location_coordinates
from app.data.sample_msp_data import populate_msp_data
from app.models.price import Location, QualityGrade, MarketType


async def test_geographic_filtering():
    """Test geographic price filtering functionality."""
    print("🧪 Testing Geographic Price Filtering")
    print("=" * 50)
    
    try:
        # 1. Populate sample data
        print("\n1. Setting up test data...")
        await populate_msp_data()
        await populate_location_coordinates()
        print("   ✅ Sample data populated")
        
        # 2. Test radius-based filtering
        print("\n2. Testing radius-based price filtering...")
        
        # Use Mumbai as center location
        mumbai_location = SAMPLE_LOCATIONS[0]  # Vashi APMC Market
        print(f"   Center: {mumbai_location.market_name}")
        print(f"   Coordinates: {mumbai_location.latitude}, {mumbai_location.longitude}")
        
        radius_result = await price_discovery_service.get_prices_within_radius(
            commodity="Rice",
            center_location=mumbai_location,
            radius_km=100,
            include_msp_comparison=True
        )
        
        print(f"   Found {radius_result.total_markets} markets within 100km")
        if radius_result.results:
            print(f"   Average price: ₹{radius_result.average_price:.2f}/quintal")
            print(f"   Price range: ₹{radius_result.price_statistics.get('min', 0):.2f} - ₹{radius_result.price_statistics.get('max', 0):.2f}")
            
            # Show distance information
            distances = [r.distance_km for r in radius_result.results if r.distance_km is not None]
            if distances:
                print(f"   Distance range: {min(distances):.1f}km - {max(distances):.1f}km")
        
        print("   ✅ Radius filtering test completed")
        
        # 3. Test market comparison within radius
        print("\n3. Testing market comparison within radius...")
        
        market_comparison = await price_discovery_service.compare_markets_within_radius(
            commodity="Rice",
            center_location=mumbai_location,
            radius_km=150
        )
        
        print(f"   Compared {len(market_comparison.markets)} markets")
        if market_comparison.best_price_market:
            print(f"   Best price market: {market_comparison.best_price_market}")
        if market_comparison.nearest_market:
            print(f"   Nearest market: {market_comparison.nearest_market}")
        
        if market_comparison.recommendations:
            print("   Recommendations:")
            for rec in market_comparison.recommendations:
                print(f"     • {rec}")
        
        print("   ✅ Market comparison test completed")
        
        # 4. Test quality-based categorization
        print("\n4. Testing quality-based price categorization...")
        
        quality_categorization = await price_discovery_service.get_quality_based_price_categorization(
            commodity="Rice",
            location="Maharashtra"
        )
        
        print(f"   Found {len(quality_categorization.categories)} quality categories")
        for category in quality_categorization.categories:
            print(f"   {category.quality_grade.value}: ₹{category.price_range['average']:.2f} avg")
            if category.price_premium_percentage is not None:
                print(f"     Premium: {category.price_premium_percentage:.1f}%")
            print(f"     Markets: {category.market_count}, Availability: {category.availability_score:.2f}")
        
        if quality_categorization.quality_recommendations:
            print("   Quality recommendations:")
            for rec in quality_categorization.quality_recommendations:
                print(f"     • {rec}")
        
        print("   ✅ Quality categorization test completed")
        
        # 5. Test location-based price variations
        print("\n5. Testing location-based price variations...")
        
        variations = await price_discovery_service.get_location_based_price_variations(
            commodity="Rice",
            center_location=mumbai_location,
            radius_km=200
        )
        
        print(f"   Analyzed {variations['total_markets_analyzed']} markets")
        
        if variations['market_type_analysis']:
            print("   Market type analysis:")
            for market_type, stats in variations['market_type_analysis'].items():
                print(f"     {market_type}: ₹{stats['average_price']:.2f} avg ({stats['market_count']} markets)")
        
        if variations['location_type_analysis']:
            print("   Location type analysis:")
            for location_type, stats in variations['location_type_analysis'].items():
                print(f"     {location_type}: ₹{stats['average_price']:.2f} avg ({stats['market_count']} markets)")
        
        if variations['recommendations']:
            print("   Recommendations:")
            for rec in variations['recommendations']:
                print(f"     • {rec}")
        
        print("   ✅ Location variations test completed")
        
        # 6. Test MSP integration
        print("\n6. Testing MSP integration...")
        
        msp_data = await price_discovery_service.get_msp_data("Rice")
        if msp_data:
            print(f"   MSP for Rice: ₹{msp_data.msp_price}/quintal")
            print(f"   Crop year: {msp_data.crop_year}")
            
            # Test price below MSP check
            test_price = 2100.0  # Below MSP
            is_below, msp_info = await price_discovery_service.check_price_below_msp("Rice", test_price)
            print(f"   Price ₹{test_price} is {'below' if is_below else 'above'} MSP")
        else:
            print("   ⚠️  No MSP data found for Rice")
        
        print("   ✅ MSP integration test completed")
        
        # 7. Test distance calculation
        print("\n7. Testing distance calculation...")
        
        location1 = SAMPLE_LOCATIONS[0]  # Mumbai
        location2 = SAMPLE_LOCATIONS[3]  # Ludhiana
        
        distance = location1.distance_to(location2)
        if distance:
            print(f"   Distance from {location1.market_name} to {location2.market_name}: {distance:.1f}km")
        else:
            print("   ⚠️  Could not calculate distance (missing coordinates)")
        
        print("   ✅ Distance calculation test completed")
        
        print("\n🎉 All geographic filtering tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_api_endpoints():
    """Test the API endpoints (requires running server)."""
    print("\n🌐 API Endpoint Test Information")
    print("=" * 50)
    
    print("To test the API endpoints, start the server and use these examples:")
    print()
    
    # Example API calls
    examples = [
        {
            "endpoint": "/api/v1/price/geographic/radius",
            "description": "Get prices within radius",
            "params": {
                "commodity": "Rice",
                "center_lat": 19.0760,
                "center_lon": 73.0777,
                "center_state": "Maharashtra",
                "center_district": "Mumbai",
                "center_market": "Vashi APMC Market",
                "radius_km": 100
            }
        },
        {
            "endpoint": "/api/v1/price/geographic/compare",
            "description": "Compare markets within radius",
            "params": {
                "commodity": "Rice",
                "center_lat": 19.0760,
                "center_lon": 73.0777,
                "center_state": "Maharashtra",
                "center_district": "Mumbai",
                "center_market": "Vashi APMC Market",
                "radius_km": 150
            }
        },
        {
            "endpoint": "/api/v1/price/quality/categorization",
            "description": "Quality-based categorization",
            "params": {
                "commodity": "Rice",
                "location": "Maharashtra"
            }
        },
        {
            "endpoint": "/api/v1/price/geographic/variations",
            "description": "Location-based price variations",
            "params": {
                "commodity": "Rice",
                "center_lat": 19.0760,
                "center_lon": 73.0777,
                "center_state": "Maharashtra",
                "center_district": "Mumbai",
                "center_market": "Vashi APMC Market",
                "radius_km": 200
            }
        },
        {
            "endpoint": "/api/v1/price/msp/integration",
            "description": "MSP integration analysis",
            "params": {
                "commodity": "Rice",
                "location": "Maharashtra"
            }
        }
    ]
    
    for example in examples:
        print(f"📍 {example['description']}")
        print(f"   GET {example['endpoint']}")
        print("   Parameters:")
        for key, value in example['params'].items():
            print(f"     {key}: {value}")
        print()


if __name__ == "__main__":
    print("🚀 Starting Geographic Price Filtering Tests")
    
    # Run the tests
    success = asyncio.run(test_geographic_filtering())
    
    if success:
        # Show API endpoint examples
        asyncio.run(test_api_endpoints())
        print("✅ All tests completed successfully!")
    else:
        print("❌ Tests failed!")
        sys.exit(1)