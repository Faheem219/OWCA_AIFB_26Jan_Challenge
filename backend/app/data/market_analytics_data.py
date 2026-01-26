"""
Sample market analytics data for festivals, weather patterns, and trade information.
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

from app.models.market_analytics import (
    FestivalCalendar, FestivalType, WeatherCondition, 
    ExportImportData, TradeDirection
)


# Festival calendar data
FESTIVAL_CALENDAR_DATA = [
    # Major National Festivals
    {
        "festival_name": "Diwali",
        "festival_type": FestivalType.RELIGIOUS.value,
        "start_date": date(2024, 11, 1),
        "end_date": date(2024, 11, 5),
        "regions": ["All India"],
        "affected_commodities": ["sugar", "ghee", "dry_fruits", "sweets", "oil"],
        "demand_multiplier": 1.4,
        "historical_impact": {
            "sugar": 25.0,
            "ghee": 30.0,
            "dry_fruits": 40.0,
            "oil": 20.0
        },
        "preparation_days": 15,
        "description": "Festival of lights, major sweet and oil consumption"
    },
    {
        "festival_name": "Holi",
        "festival_type": FestivalType.RELIGIOUS.value,
        "start_date": date(2024, 3, 13),
        "end_date": date(2024, 3, 14),
        "regions": ["North India", "Central India"],
        "affected_commodities": ["milk", "sugar", "flour", "colors"],
        "demand_multiplier": 1.3,
        "historical_impact": {
            "milk": 20.0,
            "sugar": 15.0,
            "flour": 18.0
        },
        "preparation_days": 7,
        "description": "Festival of colors, increased dairy and sweet consumption"
    },
    {
        "festival_name": "Eid",
        "festival_type": FestivalType.RELIGIOUS.value,
        "start_date": date(2024, 4, 10),
        "end_date": date(2024, 4, 12),
        "regions": ["All India"],
        "affected_commodities": ["meat", "rice", "dates", "milk", "sugar"],
        "demand_multiplier": 1.5,
        "historical_impact": {
            "meat": 35.0,
            "rice": 15.0,
            "dates": 50.0,
            "milk": 25.0
        },
        "preparation_days": 10,
        "description": "Major Islamic festival, increased meat and dairy consumption"
    },
    {
        "festival_name": "Durga Puja",
        "festival_type": FestivalType.RELIGIOUS.value,
        "start_date": date(2024, 10, 9),
        "end_date": date(2024, 10, 13),
        "regions": ["West Bengal", "Assam", "Odisha"],
        "affected_commodities": ["fish", "rice", "vegetables", "sweets"],
        "demand_multiplier": 1.6,
        "historical_impact": {
            "fish": 45.0,
            "rice": 20.0,
            "vegetables": 25.0
        },
        "preparation_days": 10,
        "description": "Major Bengali festival, high fish and rice consumption"
    },
    
    # Harvest Festivals
    {
        "festival_name": "Pongal",
        "festival_type": FestivalType.HARVEST.value,
        "start_date": date(2024, 1, 14),
        "end_date": date(2024, 1, 17),
        "regions": ["Tamil Nadu"],
        "affected_commodities": ["rice", "sugarcane", "turmeric", "milk"],
        "demand_multiplier": 1.3,
        "historical_impact": {
            "rice": 22.0,
            "sugarcane": 30.0,
            "turmeric": 25.0,
            "milk": 18.0
        },
        "preparation_days": 7,
        "description": "Tamil harvest festival celebrating rice harvest"
    },
    {
        "festival_name": "Baisakhi",
        "festival_type": FestivalType.HARVEST.value,
        "start_date": date(2024, 4, 13),
        "end_date": date(2024, 4, 14),
        "regions": ["Punjab", "Haryana"],
        "affected_commodities": ["wheat", "mustard", "sugarcane"],
        "demand_multiplier": 1.2,
        "historical_impact": {
            "wheat": 15.0,
            "mustard": 20.0,
            "sugarcane": 18.0
        },
        "preparation_days": 5,
        "description": "Punjabi harvest festival celebrating wheat harvest"
    },
    {
        "festival_name": "Onam",
        "festival_type": FestivalType.HARVEST.value,
        "start_date": date(2024, 9, 6),
        "end_date": date(2024, 9, 16),
        "regions": ["Kerala"],
        "affected_commodities": ["rice", "coconut", "vegetables", "banana"],
        "demand_multiplier": 1.4,
        "historical_impact": {
            "rice": 25.0,
            "coconut": 35.0,
            "vegetables": 20.0,
            "banana": 30.0
        },
        "preparation_days": 10,
        "description": "Kerala harvest festival with elaborate feasts"
    },
    
    # Seasonal Festivals
    {
        "festival_name": "Karva Chauth",
        "festival_type": FestivalType.SEASONAL.value,
        "start_date": date(2024, 10, 20),
        "end_date": date(2024, 10, 20),
        "regions": ["North India"],
        "affected_commodities": ["sweets", "fruits", "cosmetics"],
        "demand_multiplier": 1.2,
        "historical_impact": {
            "sweets": 15.0,
            "fruits": 12.0
        },
        "preparation_days": 3,
        "description": "Fasting festival for married women"
    },
    {
        "festival_name": "Ganesh Chaturthi",
        "festival_type": FestivalType.RELIGIOUS.value,
        "start_date": date(2024, 9, 7),
        "end_date": date(2024, 9, 17),
        "regions": ["Maharashtra", "Karnataka", "Andhra Pradesh"],
        "affected_commodities": ["modak_ingredients", "flowers", "coconut"],
        "demand_multiplier": 1.3,
        "historical_impact": {
            "coconut": 28.0,
            "flowers": 40.0
        },
        "preparation_days": 7,
        "description": "Elephant-headed god festival with sweet offerings"
    }
]


# Sample export-import data
SAMPLE_EXPORT_IMPORT_DATA = [
    # Rice exports
    {
        "commodity": "Rice",
        "trade_direction": TradeDirection.EXPORT.value,
        "country": "Bangladesh",
        "volume": 15000.0,
        "value": 7500000.0,
        "unit_price": 500.0,
        "trade_date": date.today() - timedelta(days=5),
        "port_of_entry_exit": "Kolkata Port",
        "quality_grade": "premium",
        "source": "government_data"
    },
    {
        "commodity": "Rice",
        "trade_direction": TradeDirection.EXPORT.value,
        "country": "Nepal",
        "volume": 8000.0,
        "value": 3600000.0,
        "unit_price": 450.0,
        "trade_date": date.today() - timedelta(days=3),
        "port_of_entry_exit": "Land Border",
        "quality_grade": "standard",
        "source": "government_data"
    },
    
    # Wheat imports
    {
        "commodity": "Wheat",
        "trade_direction": TradeDirection.IMPORT.value,
        "country": "Russia",
        "volume": 25000.0,
        "value": 8750000.0,
        "unit_price": 350.0,
        "trade_date": date.today() - timedelta(days=7),
        "port_of_entry_exit": "Mumbai Port",
        "quality_grade": "standard",
        "source": "government_data"
    },
    {
        "commodity": "Wheat",
        "trade_direction": TradeDirection.IMPORT.value,
        "country": "Ukraine",
        "volume": 12000.0,
        "value": 4320000.0,
        "unit_price": 360.0,
        "trade_date": date.today() - timedelta(days=10),
        "port_of_entry_exit": "Chennai Port",
        "quality_grade": "premium",
        "source": "government_data"
    },
    
    # Onion exports
    {
        "commodity": "Onion",
        "trade_direction": TradeDirection.EXPORT.value,
        "country": "UAE",
        "volume": 5000.0,
        "value": 1500000.0,
        "unit_price": 300.0,
        "trade_date": date.today() - timedelta(days=2),
        "port_of_entry_exit": "Mumbai Port",
        "quality_grade": "premium",
        "source": "government_data"
    },
    
    # Sugar exports
    {
        "commodity": "Sugar",
        "trade_direction": TradeDirection.EXPORT.value,
        "country": "Indonesia",
        "volume": 20000.0,
        "value": 12000000.0,
        "unit_price": 600.0,
        "trade_date": date.today() - timedelta(days=4),
        "port_of_entry_exit": "Mumbai Port",
        "quality_grade": "standard",
        "source": "government_data"
    },
    
    # Pulses imports
    {
        "commodity": "Pulses",
        "trade_direction": TradeDirection.IMPORT.value,
        "country": "Canada",
        "volume": 18000.0,
        "value": 14400000.0,
        "unit_price": 800.0,
        "trade_date": date.today() - timedelta(days=6),
        "port_of_entry_exit": "Chennai Port",
        "quality_grade": "premium",
        "source": "government_data"
    }
]


# Weather impact historical data
WEATHER_IMPACT_HISTORICAL_DATA = {
    "rice": [
        {
            "weather_condition": WeatherCondition.FLOOD.value,
            "year": 2023,
            "affected_regions": ["West Bengal", "Assam", "Bihar"],
            "price_impact_percentage": 18.5,
            "supply_impact_percentage": 25.0,
            "duration_days": 21,
            "description": "Monsoon floods affected kharif rice production"
        },
        {
            "weather_condition": WeatherCondition.DROUGHT.value,
            "year": 2022,
            "affected_regions": ["Maharashtra", "Karnataka"],
            "price_impact_percentage": 22.3,
            "supply_impact_percentage": 30.0,
            "duration_days": 45,
            "description": "Delayed monsoon caused drought conditions"
        }
    ],
    "wheat": [
        {
            "weather_condition": WeatherCondition.HAILSTORM.value,
            "year": 2023,
            "affected_regions": ["Punjab", "Haryana", "Uttar Pradesh"],
            "price_impact_percentage": 15.2,
            "supply_impact_percentage": 20.0,
            "duration_days": 14,
            "description": "Unseasonal hailstorm damaged standing wheat crop"
        },
        {
            "weather_condition": WeatherCondition.HEAT_WAVE.value,
            "year": 2022,
            "affected_regions": ["Rajasthan", "Gujarat"],
            "price_impact_percentage": 12.8,
            "supply_impact_percentage": 15.0,
            "duration_days": 28,
            "description": "Extreme heat affected wheat quality and yield"
        }
    ],
    "onion": [
        {
            "weather_condition": WeatherCondition.EXCESSIVE_RAIN.value,
            "year": 2023,
            "affected_regions": ["Maharashtra", "Karnataka"],
            "price_impact_percentage": 35.7,
            "supply_impact_percentage": 40.0,
            "duration_days": 18,
            "description": "Excessive rainfall damaged stored onion crop"
        }
    ]
}


# International price data (mock data for demonstration)
INTERNATIONAL_PRICES = {
    "rice": 420.0,  # USD per metric ton
    "wheat": 280.0,
    "sugar": 550.0,
    "onion": 250.0,
    "cotton": 1800.0,
    "pulses": 750.0
}


async def populate_market_analytics_data():
    """Populate database with market analytics sample data."""
    from app.db.mongodb import get_database
    
    try:
        db = await get_database()
        
        # Populate festival calendar
        festival_collection = db.festival_calendar
        await festival_collection.delete_many({})  # Clear existing data
        
        festival_documents = []
        for festival_data in FESTIVAL_CALENDAR_DATA:
            # Convert date objects to ISO strings for MongoDB
            festival_doc = festival_data.copy()
            festival_doc["start_date"] = festival_doc["start_date"].isoformat()
            festival_doc["end_date"] = festival_doc["end_date"].isoformat()
            festival_documents.append(festival_doc)
        
        if festival_documents:
            result = await festival_collection.insert_many(festival_documents)
            print(f"Inserted {len(result.inserted_ids)} festival calendar entries")
        
        # Create indexes for festival calendar
        await festival_collection.create_index([("start_date", 1), ("end_date", 1)])
        await festival_collection.create_index([("regions", 1)])
        await festival_collection.create_index([("affected_commodities", 1)])
        
        # Populate export-import data
        trade_collection = db.export_import_data
        await trade_collection.delete_many({})  # Clear existing data
        
        trade_documents = []
        for trade_data in SAMPLE_EXPORT_IMPORT_DATA:
            trade_doc = trade_data.copy()
            trade_doc["trade_date"] = trade_doc["trade_date"].isoformat()
            trade_doc["created_at"] = datetime.utcnow()
            trade_documents.append(trade_doc)
        
        if trade_documents:
            result = await trade_collection.insert_many(trade_documents)
            print(f"Inserted {len(result.inserted_ids)} export-import records")
        
        # Create indexes for trade data
        await trade_collection.create_index([("commodity", 1), ("trade_date", -1)])
        await trade_collection.create_index([("trade_direction", 1)])
        await trade_collection.create_index([("country", 1)])
        
        # Populate weather impact historical data
        weather_collection = db.weather_impact_history
        await weather_collection.delete_many({})  # Clear existing data
        
        weather_documents = []
        for commodity, impacts in WEATHER_IMPACT_HISTORICAL_DATA.items():
            for impact in impacts:
                weather_doc = impact.copy()
                weather_doc["commodity"] = commodity
                weather_doc["created_at"] = datetime.utcnow()
                weather_documents.append(weather_doc)
        
        if weather_documents:
            result = await weather_collection.insert_many(weather_documents)
            print(f"Inserted {len(result.inserted_ids)} weather impact records")
        
        # Create indexes for weather data
        await weather_collection.create_index([("commodity", 1), ("weather_condition", 1)])
        await weather_collection.create_index([("year", -1)])
        
        # Populate international prices
        intl_price_collection = db.international_prices
        await intl_price_collection.delete_many({})  # Clear existing data
        
        intl_price_documents = []
        for commodity, price in INTERNATIONAL_PRICES.items():
            intl_price_doc = {
                "commodity": commodity,
                "price_usd_per_ton": price,
                "date": date.today().isoformat(),
                "source": "mock_data",
                "created_at": datetime.utcnow()
            }
            intl_price_documents.append(intl_price_doc)
        
        if intl_price_documents:
            result = await intl_price_collection.insert_many(intl_price_documents)
            print(f"Inserted {len(result.inserted_ids)} international price records")
        
        # Create indexes for international prices
        await intl_price_collection.create_index([("commodity", 1), ("date", -1)])
        
        print("Market analytics sample data populated successfully")
        
    except Exception as e:
        print(f"Error populating market analytics data: {str(e)}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(populate_market_analytics_data())