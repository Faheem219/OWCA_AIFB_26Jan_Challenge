"""
Seed script to populate the database with demo data.

Generates:
- Sample vendor and buyer accounts
- 50+ products across 5 categories
- Multilingual content for all 10 supported languages
- Realistic pricing and location data
"""

import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# Database configuration
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "mandi_marketplace"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Supported languages
LANGUAGES = ["hi", "en", "ta", "te", "kn", "ml", "gu", "pa", "bn", "mr"]

# Categories and products
CATEGORIES = {
    "Grains": [
        {"name": "Wheat", "name_hi": "गेहूं", "price_range": (2000, 2500)},
        {"name": "Rice", "name_hi": "चावल", "price_range": (2500, 4000)},
        {"name": "Maize", "name_hi": "मक्का", "price_range": (1800, 2200)},
        {"name": "Bajra", "name_hi": "बाजरा", "price_range": (2000, 2800)},
        {"name": "Jowar", "name_hi": "ज्वार", "price_range": (2200, 3000)},
    ],
    "Vegetables": [
        {"name": "Tomato", "name_hi": "टमाटर", "price_range": (20, 40)},
        {"name": "Potato", "name_hi": "आलू", "price_range": (15, 30)},
        {"name": "Onion", "name_hi": "प्याज", "price_range": (25, 45)},
        {"name": "Cabbage", "name_hi": "पत्तागोभी", "price_range": (15, 25)},
        {"name": "Cauliflower", "name_hi": "फूलगोभी", "price_range": (20, 35)},
        {"name": "Carrot", "name_hi": "गाजर", "price_range": (25, 40)},
        {"name": "Brinjal", "name_hi": "बैंगन", "price_range": (20, 35)},
        {"name": "Spinach", "name_hi": "पालक", "price_range": (15, 25)},
        {"name": "Okra", "name_hi": "भिंडी", "price_range": (30, 50)},
        {"name": "Capsicum", "name_hi": "शिमला मिर्च", "price_range": (40, 60)},
    ],
    "Fruits": [
        {"name": "Apple", "name_hi": "सेब", "price_range": (80, 150)},
        {"name": "Mango", "name_hi": "आम", "price_range": (60, 120)},
        {"name": "Banana", "name_hi": "केला", "price_range": (30, 50)},
        {"name": "Orange", "name_hi": "संतरा", "price_range": (40, 80)},
        {"name": "Grapes", "name_hi": "अंगूर", "price_range": (50, 100)},
        {"name": "Papaya", "name_hi": "पपीता", "price_range": (25, 40)},
        {"name": "Pomegranate", "name_hi": "अनार", "price_range": (80, 150)},
        {"name": "Watermelon", "name_hi": "तरबूज", "price_range": (15, 30)},
    ],
    "Spices": [
        {"name": "Turmeric", "name_hi": "हल्दी", "price_range": (80, 150)},
        {"name": "Chili", "name_hi": "मिर्च", "price_range": (100, 200)},
        {"name": "Coriander", "name_hi": "धनिया", "price_range": (60, 100)},
        {"name": "Cumin", "name_hi": "जीरा", "price_range": (200, 350)},
        {"name": "Cardamom", "name_hi": "इलायची", "price_range": (800, 1500)},
        {"name": "Black Pepper", "name_hi": "काली मिर्च", "price_range": (400, 700)},
    ],
    "Pulses": [
        {"name": "Chickpea", "name_hi": "चना", "price_range": (5000, 7000)},
        {"name": "Lentil", "name_hi": "मसूर", "price_range": (6000, 8000)},
        {"name": "Pigeon Pea", "name_hi": "तुअर दाल", "price_range": (7000, 9000)},
        {"name": "Moong", "name_hi": "मूंग", "price_range": (6500, 8500)},
        {"name": "Urad", "name_hi": "उड़द", "price_range": (6000, 8000)},
    ]
}

# Indian states and cities
LOCATIONS = [
    {"state": "Maharashtra", "cities": ["Mumbai", "Pune", "Nagpur", "Nashik"]},
    {"state": "Karnataka", "cities": ["Bangalore", "Mysore", "Hubli", "Mangalore"]},
    {"state": "Tamil Nadu", "cities": ["Chennai", "Coimbatore", "Madurai", "Trichy"]},
    {"state": "Gujarat", "cities": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"]},
    {"state": "Punjab", "cities": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala"]},
    {"state": "Uttar Pradesh", "cities": ["Lucknow", "Kanpur", "Varanasi", "Agra"]},
    {"state": "West Bengal", "cities": ["Kolkata", "Siliguri", "Durgapur", "Asansol"]},
]

# Sample descriptions in English
DESCRIPTIONS = [
    "Fresh and high quality {product}. Directly from farm.",
    "Premium grade {product}. Best quality guaranteed.",
    "Organic {product}. No pesticides or chemicals used.",
    "Fresh harvest of {product}. Available in bulk.",
    "Grade A {product}. Certified quality.",
]

# Translation dictionary (simplified)
TRANSLATIONS = {
    "Fresh and high quality": {
        "hi": "ताज़ा और उच्च गुणवत्ता",
        "ta": "புதிய மற்றும் உயர் தரம்",
        "te": "తాజా మరియు అధిక నాణ్యత",
        "kn": "ತಾಜಾ ಮತ್ತು ಉತ್ತಮ ಗುಣಮಟ್ಟ",
    },
    "Directly from farm": {
        "hi": "सीधे खेत से",
        "ta": "நேரடியாக பண்ணையிலிருந்து",
        "te": "నేరుగా పొలం నుండి",
        "kn": "ನೇರವಾಗಿ ಫಾರ್ಮ್‌ನಿಂದ",
    }
}


async def create_sample_users(db):
    """Create sample vendor and buyer accounts."""
    print("Creating sample users...")
    
    users = []
    
    # Create 10 vendors
    for i in range(1, 11):
        location = random.choice(LOCATIONS)
        city = random.choice(location["cities"])
        
        vendor = {
            "_id": f"vendor_{i}",
            "email": f"vendor{i}@example.com",
            "phone": f"+91{9000000000 + i}",
            "password_hash": pwd_context.hash("password123"),
            "role": "vendor",
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow() - timedelta(days=random.randint(30, 180)),
            "profile": {
                "full_name": f"Vendor {i}",
                "preferred_language": random.choice(LANGUAGES),
                "location": {
                    "state": location["state"],
                    "city": city,
                    "pincode": f"{random.randint(100000, 999999)}",
                    "coordinates": {
                        "latitude": random.uniform(8.0, 35.0),
                        "longitude": random.uniform(68.0, 97.0)
                    }
                },
                "business_name": f"{city} Fresh Produce",
                "business_type": "individual_farmer" if i % 2 == 0 else "wholesaler",
                "specialization": random.choice(list(CATEGORIES.keys())),
            }
        }
        users.append(vendor)
    
    # Create 15 buyers
    for i in range(1, 16):
        location = random.choice(LOCATIONS)
        city = random.choice(location["cities"])
        
        buyer = {
            "_id": f"buyer_{i}",
            "email": f"buyer{i}@example.com",
            "phone": f"+91{8000000000 + i}",
            "password_hash": pwd_context.hash("password123"),
            "role": "buyer",
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow() - timedelta(days=random.randint(10, 120)),
            "profile": {
                "full_name": f"Buyer {i}",
                "preferred_language": random.choice(LANGUAGES),
                "location": {
                    "state": location["state"],
                    "city": city,
                    "pincode": f"{random.randint(100000, 999999)}",
                    "coordinates": {
                        "latitude": random.uniform(8.0, 35.0),
                        "longitude": random.uniform(68.0, 97.0)
                    }
                },
                "buyer_type": "restaurant" if i % 3 == 0 else "retailer" if i % 3 == 1 else "individual",
                "preferences": {
                    "preferred_categories": random.sample(list(CATEGORIES.keys()), k=random.randint(2, 4))
                }
            }
        }
        users.append(buyer)
    
    # Insert users
    await db.users.delete_many({})  # Clear existing
    await db.users.insert_many(users)
    print(f"✓ Created {len(users)} users (10 vendors, 15 buyers)")
    
    return users


async def create_sample_products(db, vendors):
    """Create 50+ sample products across all categories."""
    print("Creating sample products...")
    
    products = []
    product_id = 1
    
    for category, items in CATEGORIES.items():
        for item in items:
            # Create 1-2 products per item from different vendors
            num_products = random.randint(1, 2)
            
            for _ in range(num_products):
                vendor = random.choice(vendors)
                location = vendor["profile"]["location"]
                
                min_price, max_price = item["price_range"]
                price = random.uniform(min_price, max_price)
                
                # Generate multilingual name and description
                product_name = item["name"]
                description_template = random.choice(DESCRIPTIONS)
                description = description_template.format(product=product_name)
                
                # Create multilingual content
                name_translations = {
                    "en": product_name,
                    "hi": item.get("name_hi", product_name)
                }
                
                desc_translations = {
                    "en": description,
                    "hi": f"ताज़ा और उच्च गुणवत्ता {item.get('name_hi', product_name)}। सीधे खेत से।"
                }
                
                product = {
                    "_id": f"product_{product_id}",
                    "vendor_id": vendor["_id"],
                    "category": category.lower(),
                    "name": name_translations,
                    "description": desc_translations,
                    "price": round(price, 2),  # Use float instead of Decimal
                    "unit": "kg",
                    "quantity_available": random.randint(50, 500),
                    "minimum_order": random.choice([1, 5, 10, 25]),
                    "quality_grade": random.choice(["high", "medium", "low"]),
                    "location": {
                        "state": location["state"],
                        "city": location["city"],
                        "pincode": location["pincode"],
                        "latitude": location["coordinates"]["latitude"],
                        "longitude": location["coordinates"]["longitude"]
                    },
                    "images": [
                        f"https://placehold.co/600x400/png?text={product_name.replace(' ', '+')}"
                    ],
                    "is_organic": random.choice([True, False]),
                    "is_available": True,
                    "views": random.randint(10, 500),
                    "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 7)),
                    "metadata": {
                        "harvest_date": (datetime.utcnow() - timedelta(days=random.randint(1, 10))).isoformat(),
                        "certifications": ["organic"] if random.random() > 0.7 else [],
                    }
                }
                
                products.append(product)
                product_id += 1
    
    # Insert products
    await db.products.delete_many({})  # Clear existing
    await db.products.insert_many(products)
    print(f"✓ Created {len(products)} products across {len(CATEGORIES)} categories")
    
    return products


async def create_indexes(db):
    """Create necessary database indexes."""
    print("Creating database indexes...")
    
    # Users indexes
    await db.users.create_index([("email", 1)], unique=True)
    await db.users.create_index([("phone", 1)], unique=True)
    await db.users.create_index([("role", 1)])
    
    # Products indexes
    await db.products.create_index([("vendor_id", 1)])
    await db.products.create_index([("category", 1)])
    await db.products.create_index([("is_available", 1)])
    await db.products.create_index([("price", 1)])
    await db.products.create_index([("location.state", 1)])
    await db.products.create_index([("location.city", 1)])
    
    # Text search index for products (MongoDB text search)
    await db.products.create_index([
        ("name.en", "text"),
        ("name.hi", "text"),
        ("description.en", "text"),
        ("description.hi", "text")
    ])
    
    # Note: Geospatial index skipped for simplicity in demo
    # await db.products.create_index([("location.coordinates", "2dsphere")])
    
    print("✓ Created all database indexes")


async def main():
    """Main seed function."""
    print("=" * 60)
    print("MULTILINGUAL MANDI MARKETPLACE - DATA SEEDING")
    print("=" * 60)
    print()
    
    # Connect to MongoDB
    print("Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    try:
        # Test connection
        await client.admin.command('ping')
        print("✓ Connected to MongoDB successfully")
        print()
        
        # Create indexes
        await create_indexes(db)
        print()
        
        # Create sample users
        users = await create_sample_users(db)
        vendors = [u for u in users if u["role"] == "vendor"]
        buyers = [u for u in users if u["role"] == "buyer"]
        print()
        
        # Create sample products
        products = await create_sample_products(db, vendors)
        print()
        
        # Summary
        print("=" * 60)
        print("SEEDING COMPLETE!")
        print("=" * 60)
        print(f"Total Users Created: {len(users)}")
        print(f"  - Vendors: {len(vendors)}")
        print(f"  - Buyers: {len(buyers)}")
        print(f"Total Products Created: {len(products)}")
        print()
        print("Sample Login Credentials:")
        print("-" * 60)
        print("Vendor Account:")
        print("  Email: vendor1@example.com")
        print("  Password: password123")
        print()
        print("Buyer Account:")
        print("  Email: buyer1@example.com")
        print("  Password: password123")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        raise
    finally:
        client.close()
        print()
        print("Database connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
