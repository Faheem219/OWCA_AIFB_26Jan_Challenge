"""
Demo data seed script for Multilingual Mandi Marketplace.

This script generates:
- Sample vendor and buyer accounts
- 50+ products across 5 categories
- Multilingual content in all 10 supported languages
- Realistic pricing and location data
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.models.user import (
    UserProfile, VendorProfile, BuyerProfile, UserRole,
    BusinessType, ProductCategory as UserProductCategory,
    LocationData, UserPreferences, SupportedLanguage
)
from app.models.product import (
    Product, MultilingualText, PriceInfo, AvailabilityInfo,
    ProductMetadata, ProductLocation, ProductCategory,
    QualityGrade, ProductStatus, MeasurementUnit
)
from app.core.security import SecurityUtils

# Sample data templates
VENDOR_DATA = [
    {"name": "Rajesh Kumar", "business": "Kumar Fresh Produce", "city": "Mumbai", "state": "Maharashtra", "categories": [ProductCategory.VEGETABLES, ProductCategory.FRUITS]},
    {"name": "Priya Sharma", "business": "Sharma Organic Farms", "city": "Pune", "state": "Maharashtra", "categories": [ProductCategory.VEGETABLES, ProductCategory.GRAINS]},
    {"name": "Amit Patel", "business": "Patel Spices Trading", "city": "Ahmedabad", "state": "Gujarat", "categories": [ProductCategory.SPICES]},
    {"name": "Lakshmi Reddy", "business": "Reddy Rice Mills", "city": "Hyderabad", "state": "Telangana", "categories": [ProductCategory.GRAINS, ProductCategory.PULSES]},
    {"name": "Vijay Singh", "business": "Singh Vegetables Mart", "city": "Jaipur", "state": "Rajasthan", "categories": [ProductCategory.VEGETABLES]},
    {"name": "Meena Nair", "business": "Nair Fruits Export", "city": "Kochi", "state": "Kerala", "categories": [ProductCategory.FRUITS]},
    {"name": "Suresh Gupta", "business": "Gupta Grain House", "city": "Delhi", "state": "Delhi", "categories": [ProductCategory.GRAINS, ProductCategory.PULSES]},
    {"name": "Anjali Verma", "business": "Verma Organic Hub", "city": "Bangalore", "state": "Karnataka", "categories": [ProductCategory.VEGETABLES, ProductCategory.FRUITS]},
    {"name": "Ravi Krishnan", "business": "Krishnan Spice Garden", "city": "Chennai", "state": "Tamil Nadu", "categories": [ProductCategory.SPICES]},
    {"name": "Deepak Joshi", "business": "Joshi Fresh Market", "city": "Kolkata", "state": "West Bengal", "categories": [ProductCategory.VEGETABLES, ProductCategory.GRAINS]}
]

BUYER_DATA = [
    {"name": "Sanjay Mehta", "city": "Mumbai", "state": "Maharashtra"},
    {"name": "Kavita Desai", "city": "Pune", "state": "Maharashtra"},
    {"name": "Rahul Shah", "city": "Ahmedabad", "state": "Gujarat"},
    {"name": "Sneha Rao", "city": "Bangalore", "state": "Karnataka"},
    {"name": "Arjun Iyer", "city": "Chennai", "state": "Tamil Nadu"}
]

PRODUCT_TEMPLATES = {
    ProductCategory.VEGETABLES: [
        {"name": "Tomato", "variety": "Hybrid", "unit": MeasurementUnit.KG, "base_price": (30, 50)},
        {"name": "Potato", "variety": "Indian", "unit": MeasurementUnit.KG, "base_price": (20, 35)},
        {"name": "Onion", "variety": "Red", "unit": MeasurementUnit.KG, "base_price": (35, 55)},
        {"name": "Cabbage", "variety": "Green", "unit": MeasurementUnit.KG, "base_price": (25, 40)},
        {"name": "Cauliflower", "variety": "White", "unit": MeasurementUnit.KG, "base_price": (30, 50)},
        {"name": "Carrot", "variety": "Orange", "unit": MeasurementUnit.KG, "base_price": (40, 60)},
        {"name": "Spinach", "variety": "Fresh", "unit": MeasurementUnit.KG, "base_price": (30, 45)},
        {"name": "Brinjal", "variety": "Purple", "unit": MeasurementUnit.KG, "base_price": (35, 50)},
        {"name": "Lady Finger", "variety": "Green", "unit": MeasurementUnit.KG, "base_price": (40, 55)},
        {"name": "Green Chili", "variety": "Hot", "unit": MeasurementUnit.KG, "base_price": (50, 80)},
    ],
    ProductCategory.FRUITS: [
        {"name": "Apple", "variety": "Shimla", "unit": MeasurementUnit.KG, "base_price": (120, 180)},
        {"name": "Banana", "variety": "Robusta", "unit": MeasurementUnit.DOZEN, "base_price": (40, 60)},
        {"name": "Mango", "variety": "Alphonso", "unit": MeasurementUnit.KG, "base_price": (200, 300)},
        {"name": "Orange", "variety": "Nagpur", "unit": MeasurementUnit.KG, "base_price": (80, 120)},
        {"name": "Grapes", "variety": "Green", "unit": MeasurementUnit.KG, "base_price": (60, 100)},
        {"name": "Watermelon", "variety": "Red", "unit": MeasurementUnit.KG, "base_price": (20, 35)},
        {"name": "Pomegranate", "variety": "Ruby", "unit": MeasurementUnit.KG, "base_price": (150, 220)},
        {"name": "Papaya", "variety": "Ripe", "unit": MeasurementUnit.KG, "base_price": (30, 50)},
        {"name": "Guava", "variety": "White", "unit": MeasurementUnit.KG, "base_price": (40, 60)},
        {"name": "Pineapple", "variety": "Golden", "unit": MeasurementUnit.PIECE, "base_price": (50, 80)},
    ],
    ProductCategory.GRAINS: [
        {"name": "Rice", "variety": "Basmati", "unit": MeasurementUnit.KG, "base_price": (80, 120)},
        {"name": "Wheat", "variety": "Sharbati", "unit": MeasurementUnit.KG, "base_price": (35, 50)},
        {"name": "Maize", "variety": "Yellow", "unit": MeasurementUnit.KG, "base_price": (25, 40)},
        {"name": "Bajra", "variety": "Pearl Millet", "unit": MeasurementUnit.KG, "base_price": (40, 60)},
        {"name": "Jowar", "variety": "Sorghum", "unit": MeasurementUnit.KG, "base_price": (45, 65)},
        {"name": "Ragi", "variety": "Finger Millet", "unit": MeasurementUnit.KG, "base_price": (50, 75)},
        {"name": "Barley", "variety": "Hulled", "unit": MeasurementUnit.KG, "base_price": (55, 80)},
        {"name": "Quinoa", "variety": "White", "unit": MeasurementUnit.KG, "base_price": (300, 450)},
        {"name": "Oats", "variety": "Rolled", "unit": MeasurementUnit.KG, "base_price": (80, 120)},
        {"name": "Brown Rice", "variety": "Organic", "unit": MeasurementUnit.KG, "base_price": (100, 150)},
    ],
    ProductCategory.SPICES: [
        {"name": "Turmeric Powder", "variety": "Pure", "unit": MeasurementUnit.KG, "base_price": (150, 250)},
        {"name": "Red Chili Powder", "variety": "Hot", "unit": MeasurementUnit.KG, "base_price": (200, 300)},
        {"name": "Coriander Powder", "variety": "Ground", "unit": MeasurementUnit.KG, "base_price": (120, 180)},
        {"name": "Cumin Seeds", "variety": "Whole", "unit": MeasurementUnit.KG, "base_price": (300, 450)},
        {"name": "Black Pepper", "variety": "Whole", "unit": MeasurementUnit.KG, "base_price": (500, 750)},
        {"name": "Cardamom", "variety": "Green", "unit": MeasurementUnit.KG, "base_price": (1200, 1800)},
        {"name": "Cinnamon", "variety": "Sticks", "unit": MeasurementUnit.KG, "base_price": (400, 600)},
        {"name": "Cloves", "variety": "Whole", "unit": MeasurementUnit.KG, "base_price": (800, 1200)},
        {"name": "Mustard Seeds", "variety": "Black", "unit": MeasurementUnit.KG, "base_price": (150, 220)},
        {"name": "Fenugreek Seeds", "variety": "Dried", "unit": MeasurementUnit.KG, "base_price": (100, 150)},
    ],
    ProductCategory.PULSES: [
        {"name": "Toor Dal", "variety": "Split Pigeon Pea", "unit": MeasurementUnit.KG, "base_price": (120, 180)},
        {"name": "Moong Dal", "variety": "Split Green Gram", "unit": MeasurementUnit.KG, "base_price": (110, 160)},
        {"name": "Urad Dal", "variety": "Split Black Gram", "unit": MeasurementUnit.KG, "base_price": (130, 190)},
        {"name": "Chana Dal", "variety": "Split Chickpea", "unit": MeasurementUnit.KG, "base_price": (100, 150)},
        {"name": "Masoor Dal", "variety": "Red Lentil", "unit": MeasurementUnit.KG, "base_price": (90, 140)},
        {"name": "Rajma", "variety": "Red Kidney Beans", "unit": MeasurementUnit.KG, "base_price": (150, 220)},
        {"name": "Kabuli Chana", "variety": "White Chickpea", "unit": MeasurementUnit.KG, "base_price": (120, 180)},
        {"name": "Whole Moong", "variety": "Green Gram", "unit": MeasurementUnit.KG, "base_price": (110, 160)},
        {"name": "Black Eyed Peas", "variety": "Lobia", "unit": MeasurementUnit.KG, "base_price": (100, 150)},
        {"name": "Soybean", "variety": "Yellow", "unit": MeasurementUnit.KG, "base_price": (80, 120)},
    ]
}

# Translation data (simplified - using predefined translations from translation service)
TRANSLATIONS = {
    "en": lambda x: x,  # English - no translation needed
}


async def create_multilingual_text(text_en: str, language: SupportedLanguage = SupportedLanguage.ENGLISH) -> MultilingualText:
    """Create multilingual text with English as base and mock translations."""
    # For demo purposes, we'll use the same text for all languages
    # In production, this would call the translation service
    translations = {
        SupportedLanguage.ENGLISH: text_en,
        SupportedLanguage.HINDI: text_en,  # In real scenario, would be translated
        SupportedLanguage.TAMIL: text_en,
        SupportedLanguage.TELUGU: text_en,
        SupportedLanguage.KANNADA: text_en,
        SupportedLanguage.MALAYALAM: text_en,
        SupportedLanguage.GUJARATI: text_en,
        SupportedLanguage.PUNJABI: text_en,
        SupportedLanguage.BENGALI: text_en,
        SupportedLanguage.MARATHI: text_en,
    }
    
    return MultilingualText(
        original_text=text_en,
        original_language=language,
        translations=translations
    )


async def seed_database():
    """Seed the database with demo data."""
    print("Starting database seeding...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]
    
    # Clear existing data (optional - comment out to preserve existing data)
    print("Clearing existing demo data...")
    await db.users.delete_many({"email": {"$regex": "@demo.mandi"}})
    await db.products.delete_many({"vendor_id": {"$regex": "demo_vendor_"}})
    
    # Create vendor accounts
    print(f"\nCreating {len(VENDOR_DATA)} vendor accounts...")
    vendors = []
    for i, vendor_data in enumerate(VENDOR_DATA):
        user_id = f"demo_vendor_{i+1}"
        email = f"{vendor_data['name'].lower().replace(' ', '.')}@demo.mandi"
        
        vendor_profile = VendorProfile(
            business_name=vendor_data["business"],
            business_type=BusinessType.INDIVIDUAL,
            product_categories=[cat.value for cat in vendor_data["categories"]],
            market_location=f"{vendor_data['city']} Mandi",
            verification_documents=["demo_doc.pdf"]
        )
        
        location = LocationData(
            address=f"Market Road, {vendor_data['city']}",
            city=vendor_data["city"],
            state=vendor_data["state"],
            pincode="000000",
            country="India",
            coordinates=[77.2090, 28.6139]  # Default coordinates
        )
        
        user = {
            "_id": user_id,
            "email": email,
            "full_name": vendor_data["name"],
            "phone_number": f"+91{9000000000 + i}",
            "password_hash": SecurityUtils.hash_password("DemoPassword123!"),
            "role": UserRole.VENDOR.value,
            "vendor_profile": vendor_profile.dict(),
            "location": location.dict(),
            "preferences": UserPreferences(language=SupportedLanguage.ENGLISH).dict(),
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.users.insert_one(user)
        vendors.append({"id": user_id, "data": vendor_data})
        print(f"  ✓ Created vendor: {vendor_data['name']} - {vendor_data['business']}")
    
    # Create buyer accounts
    print(f"\nCreating {len(BUYER_DATA)} buyer accounts...")
    for i, buyer_data in enumerate(BUYER_DATA):
        user_id = f"demo_buyer_{i+1}"
        email = f"{buyer_data['name'].lower().replace(' ', '.')}@demo.mandi"
        
        buyer_profile = BuyerProfile(
            buyer_type="individual",
            preferred_categories=[cat.value for cat in ProductCategory]
        )
        
        location = LocationData(
            address=f"Residential Area, {buyer_data['city']}",
            city=buyer_data["city"],
            state=buyer_data["state"],
            pincode="000000",
            country="India",
            coordinates=[77.2090, 28.6139]
        )
        
        user = {
            "_id": user_id,
            "email": email,
            "full_name": buyer_data["name"],
            "phone_number": f"+91{9100000000 + i}",
            "password_hash": SecurityUtils.hash_password("DemoPassword123!"),
            "role": UserRole.BUYER.value,
            "buyer_profile": buyer_profile.dict(),
            "location": location.dict(),
            "preferences": UserPreferences(language=SupportedLanguage.ENGLISH).dict(),
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.users.insert_one(user)
        print(f"  ✓ Created buyer: {buyer_data['name']}")
    
    # Create products
    print(f"\nCreating 50+ products across categories...")
    product_count = 0
    
    for vendor in vendors:
        vendor_id = vendor["id"]
        vendor_categories = vendor["data"]["categories"]
        vendor_city = vendor["data"]["city"]
        vendor_state = vendor["data"]["state"]
        
        # Create 5-7 products per vendor
        products_per_vendor = random.randint(5, 7)
        
        for _ in range(products_per_vendor):
            # Select a random category from vendor's categories
            category = random.choice(vendor_categories)
            
            # Select a random product template from that category
            template = random.choice(PRODUCT_TEMPLATES[category])
            
            product_id = f"demo_product_{product_count + 1:03d}"
            
            # Generate price
            min_price, max_price = template["base_price"]
            base_price = Decimal(str(random.randint(min_price, max_price)))
            
            # Create product name and description
            name_text = f"Fresh {template['name']} - {template['variety']}"
            desc_text = f"High quality {template['name']} ({template['variety']} variety) sourced from local farms. Perfect for cooking and consumption."
            
            name = await create_multilingual_text(name_text)
            description = await create_multilingual_text(desc_text)
            
            # Product location
            location = ProductLocation(
                address=f"{vendor_city} Mandi, Market Road",
                city=vendor_city,
                state=vendor_state,
                pincode="000000",
                country="India",
                coordinates=[77.2090 + random.uniform(-1, 1), 28.6139 + random.uniform(-1, 1)],
                market_name=f"{vendor_city} Central Mandi"
            )
            
            # Price info
            price_info = PriceInfo(
                base_price=base_price,
                currency="INR",
                negotiable=random.choice([True, False]),
                bulk_discount=random.choice([None, {"min_quantity": 50, "discount_percent": 10}])
            )
            
            # Availability
            availability = AvailabilityInfo(
                quantity_available=random.randint(10, 500),
                unit=template["unit"],
                minimum_order=random.randint(1, 10)
            )
            
            # Metadata
            metadata = ProductMetadata(
                origin=vendor_state,
                variety=template["variety"],
                harvest_date=datetime.utcnow() - timedelta(days=random.randint(1, 10)),
                shelf_life_days=random.randint(5, 30) if category in [ProductCategory.VEGETABLES, ProductCategory.FRUITS] else None,
                certifications=["organic"] if random.random() > 0.7 else []
            )
            
            # Quality grade
            quality_grade = random.choices(
                [QualityGrade.PREMIUM, QualityGrade.GRADE_A, QualityGrade.GRADE_B, QualityGrade.ORGANIC],
                weights=[0.2, 0.4, 0.3, 0.1]
            )[0]
            
            product = {
                "_id": product_id,
                "product_id": product_id,
                "vendor_id": vendor_id,
                "name": name.dict(),
                "description": description.dict(),
                "category": category.value,
                "subcategory": template["variety"],
                "price_info": price_info.dict(),
                "availability": availability.dict(),
                "location": location.dict(),
                "metadata": metadata.dict(),
                "quality_grade": quality_grade.value,
                "status": ProductStatus.ACTIVE.value,
                "tags": [template["name"].lower(), template["variety"].lower(), category.value.lower()],
                "images": [],
                "featured": random.random() > 0.8,
                "views_count": random.randint(0, 100),
                "favorites_count": random.randint(0, 20),
                "created_at": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                "updated_at": datetime.utcnow()
            }
            
            await db.products.insert_one(product)
            product_count += 1
            
            if product_count % 10 == 0:
                print(f"  ✓ Created {product_count} products...")
    
    print(f"\n✓ Successfully created {product_count} products!")
    
    # Summary
    print("\n" + "="*60)
    print("DATABASE SEEDING COMPLETED")
    print("="*60)
    print(f"Vendors created: {len(VENDOR_DATA)}")
    print(f"Buyers created: {len(BUYER_DATA)}")
    print(f"Products created: {product_count}")
    print("\nDemo Credentials:")
    print("  Email: any vendor/buyer email @demo.mandi")
    print("  Password: DemoPassword123!")
    print("\nExample vendors:")
    for vendor in vendors[:3]:
        email = f"{vendor['data']['name'].lower().replace(' ', '.')}@demo.mandi"
        print(f"  - {vendor['data']['name']}: {email}")
    print("="*60)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
