"""
Sample seasonal factors data for price prediction.
"""
from app.models.price import SeasonalFactor

# Seasonal factors for major commodities (1.0 = normal, >1.0 = higher prices, <1.0 = lower prices)
SEASONAL_FACTORS_DATA = {
    "Rice": [
        SeasonalFactor(month=1, factor=1.0, description="Post-harvest season, stable prices"),
        SeasonalFactor(month=2, factor=1.0, description="Stable supply, normal prices"),
        SeasonalFactor(month=3, factor=0.95, description="Good supply from rabi harvest"),
        SeasonalFactor(month=4, factor=0.9, description="Peak harvest season, lower prices"),
        SeasonalFactor(month=5, factor=0.95, description="Post-harvest, increasing demand"),
        SeasonalFactor(month=6, factor=1.1, description="Monsoon season, supply concerns"),
        SeasonalFactor(month=7, factor=1.2, description="Monsoon peak, transportation issues"),
        SeasonalFactor(month=8, factor=1.1, description="Kharif growing season"),
        SeasonalFactor(month=9, factor=1.0, description="Pre-harvest, moderate prices"),
        SeasonalFactor(month=10, factor=0.9, description="Kharif harvest begins"),
        SeasonalFactor(month=11, factor=0.9, description="Peak harvest season"),
        SeasonalFactor(month=12, factor=1.0, description="Festival season demand")
    ],
    
    "Wheat": [
        SeasonalFactor(month=1, factor=0.9, description="Rabi growing season, good supply"),
        SeasonalFactor(month=2, factor=0.9, description="Pre-harvest, stable supply"),
        SeasonalFactor(month=3, factor=0.95, description="Harvest preparation"),
        SeasonalFactor(month=4, factor=1.2, description="Peak harvest season, procurement"),
        SeasonalFactor(month=5, factor=1.1, description="Post-harvest, government buying"),
        SeasonalFactor(month=6, factor=1.0, description="Summer season, stable prices"),
        SeasonalFactor(month=7, factor=0.9, description="Good stock availability"),
        SeasonalFactor(month=8, factor=0.9, description="Monsoon season, adequate supply"),
        SeasonalFactor(month=9, factor=0.9, description="Post-monsoon, stable supply"),
        SeasonalFactor(month=10, factor=0.95, description="Festival season demand"),
        SeasonalFactor(month=11, factor=1.0, description="Winter season begins"),
        SeasonalFactor(month=12, factor=1.0, description="Year-end demand")
    ],
    
    "Onion": [
        SeasonalFactor(month=1, factor=1.2, description="Winter demand, limited supply"),
        SeasonalFactor(month=2, factor=1.3, description="Peak winter demand"),
        SeasonalFactor(month=3, factor=1.1, description="Late rabi harvest begins"),
        SeasonalFactor(month=4, factor=0.9, description="Rabi harvest peak"),
        SeasonalFactor(month=5, factor=0.8, description="Good supply from rabi"),
        SeasonalFactor(month=6, factor=0.9, description="Summer storage period"),
        SeasonalFactor(month=7, factor=1.0, description="Monsoon season"),
        SeasonalFactor(month=8, factor=1.1, description="Kharif growing, storage depletion"),
        SeasonalFactor(month=9, factor=1.2, description="Pre-harvest, low supply"),
        SeasonalFactor(month=10, factor=1.3, description="Festival demand, supply gap"),
        SeasonalFactor(month=11, factor=1.2, description="Kharif harvest begins"),
        SeasonalFactor(month=12, factor=1.1, description="Winter demand increases")
    ],
    
    "Potato": [
        SeasonalFactor(month=1, factor=0.8, description="Peak harvest season"),
        SeasonalFactor(month=2, factor=0.9, description="Good supply from harvest"),
        SeasonalFactor(month=3, factor=1.0, description="Post-harvest, normal prices"),
        SeasonalFactor(month=4, factor=1.1, description="Summer demand increases"),
        SeasonalFactor(month=5, factor=1.2, description="Hot weather, storage issues"),
        SeasonalFactor(month=6, factor=1.1, description="Pre-monsoon demand"),
        SeasonalFactor(month=7, factor=1.0, description="Monsoon season"),
        SeasonalFactor(month=8, factor=0.9, description="New crop planting"),
        SeasonalFactor(month=9, factor=0.8, description="Early harvest varieties"),
        SeasonalFactor(month=10, factor=0.9, description="Harvest season begins"),
        SeasonalFactor(month=11, factor=1.0, description="Festival season demand"),
        SeasonalFactor(month=12, factor=1.0, description="Winter demand stable")
    ],
    
    "Tomato": [
        SeasonalFactor(month=1, factor=1.1, description="Winter crop, good demand"),
        SeasonalFactor(month=2, factor=1.2, description="Peak winter demand"),
        SeasonalFactor(month=3, factor=1.0, description="Spring season, moderate supply"),
        SeasonalFactor(month=4, factor=0.9, description="Summer crop harvest"),
        SeasonalFactor(month=5, factor=0.8, description="Peak summer harvest"),
        SeasonalFactor(month=6, factor=0.9, description="Pre-monsoon supply"),
        SeasonalFactor(month=7, factor=1.0, description="Monsoon season, transport issues"),
        SeasonalFactor(month=8, factor=1.1, description="Monsoon peak, supply disruption"),
        SeasonalFactor(month=9, factor=1.2, description="Post-monsoon, limited supply"),
        SeasonalFactor(month=10, factor=1.1, description="Festival demand"),
        SeasonalFactor(month=11, factor=1.0, description="Winter crop planting"),
        SeasonalFactor(month=12, factor=1.0, description="Year-end demand")
    ],
    
    "Cotton": [
        SeasonalFactor(month=1, factor=1.0, description="Post-harvest, market activity"),
        SeasonalFactor(month=2, factor=1.0, description="Marketing season peak"),
        SeasonalFactor(month=3, factor=0.95, description="Good supply availability"),
        SeasonalFactor(month=4, factor=0.9, description="Marketing season continues"),
        SeasonalFactor(month=5, factor=0.9, description="Summer season, stable prices"),
        SeasonalFactor(month=6, factor=0.95, description="Pre-monsoon, sowing preparation"),
        SeasonalFactor(month=7, factor=1.0, description="Sowing season begins"),
        SeasonalFactor(month=8, factor=1.0, description="Growing season"),
        SeasonalFactor(month=9, factor=1.0, description="Crop development phase"),
        SeasonalFactor(month=10, factor=1.05, description="Pre-harvest, market anticipation"),
        SeasonalFactor(month=11, factor=1.1, description="Harvest begins, quality assessment"),
        SeasonalFactor(month=12, factor=1.05, description="Peak harvest season")
    ],
    
    "Sugar": [
        SeasonalFactor(month=1, factor=0.95, description="Crushing season peak"),
        SeasonalFactor(month=2, factor=0.9, description="Good production, ample supply"),
        SeasonalFactor(month=3, factor=0.9, description="Crushing season continues"),
        SeasonalFactor(month=4, factor=0.95, description="Season ending, stock building"),
        SeasonalFactor(month=5, factor=1.0, description="Off-season begins"),
        SeasonalFactor(month=6, factor=1.05, description="Summer demand increases"),
        SeasonalFactor(month=7, factor=1.1, description="Monsoon season, transport costs"),
        SeasonalFactor(month=8, factor=1.1, description="Festival season preparation"),
        SeasonalFactor(month=9, factor=1.15, description="Festival demand peak"),
        SeasonalFactor(month=10, factor=1.2, description="Post-festival, pre-season"),
        SeasonalFactor(month=11, factor=1.1, description="New season preparation"),
        SeasonalFactor(month=12, factor=1.0, description="New crushing season begins")
    ],
    
    "Turmeric": [
        SeasonalFactor(month=1, factor=1.0, description="Post-harvest marketing"),
        SeasonalFactor(month=2, factor=0.95, description="Good supply from harvest"),
        SeasonalFactor(month=3, factor=0.9, description="Peak marketing season"),
        SeasonalFactor(month=4, factor=0.9, description="Ample supply, lower prices"),
        SeasonalFactor(month=5, factor=0.95, description="Summer season, stable demand"),
        SeasonalFactor(month=6, factor=1.0, description="Pre-monsoon, normal prices"),
        SeasonalFactor(month=7, factor=1.05, description="Monsoon season, transport issues"),
        SeasonalFactor(month=8, factor=1.1, description="Growing season, reduced supply"),
        SeasonalFactor(month=9, factor=1.15, description="Festival season demand"),
        SeasonalFactor(month=10, factor=1.2, description="Pre-harvest, supply tightness"),
        SeasonalFactor(month=11, factor=1.1, description="Harvest preparation"),
        SeasonalFactor(month=12, factor=1.05, description="Early harvest, quality premium")
    ]
}


async def populate_seasonal_factors():
    """Populate database with seasonal factors data."""
    from app.db.mongodb import get_database
    
    try:
        db = await get_database()
        collection = db.seasonal_factors
        
        # Clear existing data
        await collection.delete_many({})
        
        # Insert seasonal factors for each commodity
        total_inserted = 0
        
        for commodity, factors in SEASONAL_FACTORS_DATA.items():
            factor_documents = []
            for factor in factors:
                doc = factor.dict()
                doc["commodity"] = commodity
                factor_documents.append(doc)
            
            result = await collection.insert_many(factor_documents)
            total_inserted += len(result.inserted_ids)
            print(f"Inserted {len(result.inserted_ids)} seasonal factors for {commodity}")
        
        print(f"Total seasonal factors inserted: {total_inserted}")
        
        # Create indexes
        await collection.create_index([("commodity", 1), ("month", 1)], unique=True)
        await collection.create_index([("commodity", 1)])
        
        print("Seasonal factors indexes created")
        
    except Exception as e:
        print(f"Error populating seasonal factors: {str(e)}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(populate_seasonal_factors())