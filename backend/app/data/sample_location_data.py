"""
Sample location data with coordinates for testing geographic functionality.
"""
from app.models.price import Location

# Sample locations with coordinates for major Indian markets
SAMPLE_LOCATIONS = [
    # Maharashtra
    Location(
        state="Maharashtra",
        district="Mumbai",
        market_name="Vashi APMC Market",
        latitude=19.0760,
        longitude=73.0777,
        pincode="400703"
    ),
    Location(
        state="Maharashtra",
        district="Pune",
        market_name="Pune APMC Market",
        latitude=18.5204,
        longitude=73.8567,
        pincode="411001"
    ),
    Location(
        state="Maharashtra",
        district="Nashik",
        market_name="Nashik APMC Market",
        latitude=19.9975,
        longitude=73.7898,
        pincode="422001"
    ),
    
    # Punjab
    Location(
        state="Punjab",
        district="Ludhiana",
        market_name="Ludhiana Grain Market",
        latitude=30.9010,
        longitude=75.8573,
        pincode="141001"
    ),
    Location(
        state="Punjab",
        district="Amritsar",
        market_name="Amritsar Mandi",
        latitude=31.6340,
        longitude=74.8723,
        pincode="143001"
    ),
    Location(
        state="Punjab",
        district="Jalandhar",
        market_name="Jalandhar APMC",
        latitude=31.3260,
        longitude=75.5762,
        pincode="144001"
    ),
    
    # Uttar Pradesh
    Location(
        state="Uttar Pradesh",
        district="Lucknow",
        market_name="Lucknow Wholesale Market",
        latitude=26.8467,
        longitude=80.9462,
        pincode="226001"
    ),
    Location(
        state="Uttar Pradesh",
        district="Kanpur",
        market_name="Kanpur Grain Market",
        latitude=26.4499,
        longitude=80.3319,
        pincode="208001"
    ),
    Location(
        state="Uttar Pradesh",
        district="Agra",
        market_name="Agra APMC Market",
        latitude=27.1767,
        longitude=78.0081,
        pincode="282001"
    ),
    
    # Karnataka
    Location(
        state="Karnataka",
        district="Bangalore",
        market_name="Bangalore APMC Market",
        latitude=12.9716,
        longitude=77.5946,
        pincode="560001"
    ),
    Location(
        state="Karnataka",
        district="Mysore",
        market_name="Mysore Wholesale Market",
        latitude=12.2958,
        longitude=76.6394,
        pincode="570001"
    ),
    Location(
        state="Karnataka",
        district="Hubli",
        market_name="Hubli APMC Market",
        latitude=15.3647,
        longitude=75.1240,
        pincode="580001"
    ),
    
    # Tamil Nadu
    Location(
        state="Tamil Nadu",
        district="Chennai",
        market_name="Chennai Koyambedu Market",
        latitude=13.0827,
        longitude=80.2707,
        pincode="600001"
    ),
    Location(
        state="Tamil Nadu",
        district="Coimbatore",
        market_name="Coimbatore APMC Market",
        latitude=11.0168,
        longitude=76.9558,
        pincode="641001"
    ),
    Location(
        state="Tamil Nadu",
        district="Madurai",
        market_name="Madurai Wholesale Market",
        latitude=9.9252,
        longitude=78.1198,
        pincode="625001"
    ),
    
    # Gujarat
    Location(
        state="Gujarat",
        district="Ahmedabad",
        market_name="Ahmedabad APMC Market",
        latitude=23.0225,
        longitude=72.5714,
        pincode="380001"
    ),
    Location(
        state="Gujarat",
        district="Surat",
        market_name="Surat APMC Market",
        latitude=21.1702,
        longitude=72.8311,
        pincode="395001"
    ),
    Location(
        state="Gujarat",
        district="Rajkot",
        market_name="Rajkot Grain Market",
        latitude=22.3039,
        longitude=70.8022,
        pincode="360001"
    ),
    
    # Rajasthan
    Location(
        state="Rajasthan",
        district="Jaipur",
        market_name="Jaipur APMC Market",
        latitude=26.9124,
        longitude=75.7873,
        pincode="302001"
    ),
    Location(
        state="Rajasthan",
        district="Jodhpur",
        market_name="Jodhpur Wholesale Market",
        latitude=26.2389,
        longitude=73.0243,
        pincode="342001"
    ),
    Location(
        state="Rajasthan",
        district="Kota",
        market_name="Kota APMC Market",
        latitude=25.2138,
        longitude=75.8648,
        pincode="324001"
    ),
    
    # West Bengal
    Location(
        state="West Bengal",
        district="Kolkata",
        market_name="Kolkata Wholesale Market",
        latitude=22.5726,
        longitude=88.3639,
        pincode="700001"
    ),
    Location(
        state="West Bengal",
        district="Siliguri",
        market_name="Siliguri APMC Market",
        latitude=26.7271,
        longitude=88.3953,
        pincode="734001"
    ),
    
    # Haryana
    Location(
        state="Haryana",
        district="Gurgaon",
        market_name="Gurgaon APMC Market",
        latitude=28.4595,
        longitude=77.0266,
        pincode="122001"
    ),
    Location(
        state="Haryana",
        district="Faridabad",
        market_name="Faridabad Grain Market",
        latitude=28.4089,
        longitude=77.3178,
        pincode="121001"
    ),
    
    # Madhya Pradesh
    Location(
        state="Madhya Pradesh",
        district="Bhopal",
        market_name="Bhopal APMC Market",
        latitude=23.2599,
        longitude=77.4126,
        pincode="462001"
    ),
    Location(
        state="Madhya Pradesh",
        district="Indore",
        market_name="Indore Wholesale Market",
        latitude=22.7196,
        longitude=75.8577,
        pincode="452001"
    )
]


async def populate_location_coordinates():
    """
    Update existing price data with coordinates from sample locations.
    """
    from app.db.mongodb import get_database
    
    try:
        db = await get_database()
        collection = db.price_data
        
        updated_count = 0
        
        for location in SAMPLE_LOCATIONS:
            # Update price data with coordinates
            result = await collection.update_many(
                {
                    "location.state": {"$regex": location.state, "$options": "i"},
                    "location.district": {"$regex": location.district, "$options": "i"},
                    "location.latitude": {"$exists": False}
                },
                {
                    "$set": {
                        "location.latitude": location.latitude,
                        "location.longitude": location.longitude,
                        "location.pincode": location.pincode
                    }
                }
            )
            
            updated_count += result.modified_count
        
        print(f"Updated {updated_count} price records with coordinates")
        
        # Create geospatial index for efficient location queries
        await collection.create_index([("location.latitude", 1), ("location.longitude", 1)])
        print("Created geospatial index for location queries")
        
    except Exception as e:
        print(f"Error updating location coordinates: {str(e)}")
        raise


def get_location_by_name(state: str, district: str = None) -> Location:
    """
    Get a sample location by state and optionally district.
    
    Args:
        state: State name
        district: Optional district name
        
    Returns:
        Location object with coordinates
    """
    for location in SAMPLE_LOCATIONS:
        if location.state.lower() == state.lower():
            if district is None or location.district.lower() == district.lower():
                return location
    
    # Return a default location if not found
    return SAMPLE_LOCATIONS[0]  # Default to first location


if __name__ == "__main__":
    import asyncio
    asyncio.run(populate_location_coordinates())