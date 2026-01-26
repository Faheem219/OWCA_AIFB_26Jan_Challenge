"""
Sample MSP (Minimum Support Price) data for testing.
"""
from datetime import date
from app.models.price import MSPData

# Sample MSP data for major crops (2024-25 crop year)
SAMPLE_MSP_DATA = [
    MSPData(
        commodity="Rice",
        crop_year="2024-25",
        msp_price=2300.0,  # Rs per quintal
        effective_from=date(2024, 10, 1),
        effective_to=date(2025, 9, 30),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Wheat",
        crop_year="2024-25",
        msp_price=2425.0,
        effective_from=date(2024, 4, 1),
        effective_to=date(2025, 3, 31),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Paddy",
        crop_year="2024-25",
        msp_price=2300.0,
        effective_from=date(2024, 10, 1),
        effective_to=date(2025, 9, 30),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Jowar",
        crop_year="2024-25",
        msp_price=3180.0,
        effective_from=date(2024, 10, 1),
        effective_to=date(2025, 9, 30),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Bajra",
        crop_year="2024-25",
        msp_price=2500.0,
        effective_from=date(2024, 10, 1),
        effective_to=date(2025, 9, 30),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Maize",
        crop_year="2024-25",
        msp_price=2090.0,
        effective_from=date(2024, 10, 1),
        effective_to=date(2025, 9, 30),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Cotton",
        crop_year="2024-25",
        msp_price=7121.0,
        effective_from=date(2024, 10, 1),
        effective_to=date(2025, 9, 30),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Sugarcane",
        crop_year="2024-25",
        msp_price=340.0,  # Rs per quintal
        effective_from=date(2024, 10, 1),
        effective_to=date(2025, 9, 30),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Groundnut",
        crop_year="2024-25",
        msp_price=6377.0,
        effective_from=date(2024, 10, 1),
        effective_to=date(2025, 9, 30),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Soybean",
        crop_year="2024-25",
        msp_price=4892.0,
        effective_from=date(2024, 10, 1),
        effective_to=date(2025, 9, 30),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Sunflower",
        crop_year="2024-25",
        msp_price=6760.0,
        effective_from=date(2024, 10, 1),
        effective_to=date(2025, 9, 30),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Mustard",
        crop_year="2024-25",
        msp_price=5650.0,
        effective_from=date(2024, 4, 1),
        effective_to=date(2025, 3, 31),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Safflower",
        crop_year="2024-25",
        msp_price=5800.0,
        effective_from=date(2024, 10, 1),
        effective_to=date(2025, 9, 30),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Gram",
        crop_year="2024-25",
        msp_price=5440.0,
        effective_from=date(2024, 4, 1),
        effective_to=date(2025, 3, 31),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Tur",
        crop_year="2024-25",
        msp_price=7550.0,
        effective_from=date(2024, 10, 1),
        effective_to=date(2025, 9, 30),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Moong",
        crop_year="2024-25",
        msp_price=8558.0,
        effective_from=date(2024, 10, 1),
        effective_to=date(2025, 9, 30),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Urad",
        crop_year="2024-25",
        msp_price=7400.0,
        effective_from=date(2024, 10, 1),
        effective_to=date(2025, 9, 30),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Linseed",
        crop_year="2024-25",
        msp_price=7749.0,
        effective_from=date(2024, 4, 1),
        effective_to=date(2025, 3, 31),
        unit="quintal",
        source="government"
    ),
    MSPData(
        commodity="Barley",
        crop_year="2024-25",
        msp_price=1735.0,
        effective_from=date(2024, 4, 1),
        effective_to=date(2025, 3, 31),
        unit="quintal",
        source="government"
    )
]


async def populate_msp_data():
    """Populate database with sample MSP data."""
    from app.db.mongodb import get_database
    
    try:
        db = await get_database()
        collection = db.msp_data
        
        # Clear existing data
        await collection.delete_many({})
        
        # Insert sample data
        msp_documents = [msp.dict() for msp in SAMPLE_MSP_DATA]
        result = await collection.insert_many(msp_documents)
        
        print(f"Inserted {len(result.inserted_ids)} MSP records")
        
        # Create indexes
        await collection.create_index([("commodity", 1), ("crop_year", 1)], unique=True)
        await collection.create_index([("effective_from", 1), ("effective_to", 1)])
        
        print("MSP data indexes created")
        
    except Exception as e:
        print(f"Error populating MSP data: {str(e)}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(populate_msp_data())