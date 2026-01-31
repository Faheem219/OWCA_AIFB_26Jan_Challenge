"""
Database seed script for Multilingual Mandi Marketplace.
Creates proper data structures matching the backend models.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, date
from decimal import Decimal
import random

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from bson import ObjectId

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database configuration  
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/mandi_marketplace")
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "mandi_marketplace")

# Supported languages
LANGUAGES = {
    "hi": "Hindi",
    "en": "English", 
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "bn": "Bengali",
    "mr": "Marathi"
}

# Sample vendors
VENDOR_DATA = [
    {
        "name": "Rajesh Kumar",
        "business": "Kumar Fresh Produce",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400001",
        "categories": ["vegetables", "fruits"],
        "lat": 19.0760, "lon": 72.8777
    },
    {
        "name": "Priya Sharma",
        "business": "Sharma Organic Farms",
        "city": "Pune",
        "state": "Maharashtra",
        "pincode": "411001",
        "categories": ["vegetables", "grains"],
        "lat": 18.5204, "lon": 73.8567
    },
    {
        "name": "Amit Patel",
        "business": "Patel Spices Trading",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "pincode": "380001",
        "categories": ["spices"],
        "lat": 23.0225, "lon": 72.5714
    },
    {
        "name": "Lakshmi Reddy",
        "business": "Reddy Rice Mills",
        "city": "Hyderabad",
        "state": "Telangana",
        "pincode": "500001",
        "categories": ["grains", "dairy"],
        "lat": 17.3850, "lon": 78.4867
    },
    {
        "name": "Vijay Singh",
        "business": "Singh Vegetables Mart",
        "city": "Jaipur",
        "state": "Rajasthan",
        "pincode": "302001",
        "categories": ["vegetables"],
        "lat": 26.9124, "lon": 75.7873
    },
    {
        "name": "Meena Nair",
        "business": "Nair Fruits Export",
        "city": "Kochi",
        "state": "Kerala",
        "pincode": "682001",
        "categories": ["fruits"],
        "lat": 9.9312, "lon": 76.2673
    },
    {
        "name": "Suresh Gupta",
        "business": "Gupta Grain House",
        "city": "Delhi",
        "state": "Delhi",
        "pincode": "110001",
        "categories": ["grains", "dairy"],
        "lat": 28.6139, "lon": 77.2090
    },
    {
        "name": "Anjali Verma",
        "business": "Verma Organic Hub",
        "city": "Bangalore",
        "state": "Karnataka",
        "pincode": "560001",
        "categories": ["vegetables", "fruits"],
        "lat": 12.9716, "lon": 77.5946
    },
    {
        "name": "Ravi Krishnan",
        "business": "Krishnan Spice Garden",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "pincode": "600001",
        "categories": ["spices"],
        "lat": 13.0827, "lon": 80.2707
    },
    {
        "name": "Deepak Joshi",
        "business": "Joshi Fresh Market",
        "city": "Kolkata",
        "state": "West Bengal",
        "pincode": "700001",
        "categories": ["vegetables", "grains"],
        "lat": 22.5726, "lon": 88.3639
    }
]

# Sample buyers
BUYER_DATA = [
    {"name": "Sanjay Mehta", "city": "Mumbai", "state": "Maharashtra", "pincode": "400002", "lat": 19.0456, "lon": 72.8843},
    {"name": "Kavita Desai", "city": "Pune", "state": "Maharashtra", "pincode": "411002", "lat": 18.5109, "lon": 73.8477},
    {"name": "Rahul Shah", "city": "Ahmedabad", "state": "Gujarat", "pincode": "380002", "lat": 23.0339, "lon": 72.5852},
    {"name": "Sneha Rao", "city": "Bangalore", "state": "Karnataka", "pincode": "560002", "lat": 12.9819, "lon": 77.5973},
    {"name": "Arjun Iyer", "city": "Chennai", "state": "Tamil Nadu", "pincode": "600002", "lat": 13.0934, "lon": 80.2749},
]

# Product templates with proper structure
PRODUCT_TEMPLATES = {
    "vegetables": [
        {"name_en": "Fresh Tomatoes", "name_hi": "ताज़े टमाटर", "variety": "Hybrid Red", "base_price": (25, 45), "unit": "kg"},
        {"name_en": "Organic Potatoes", "name_hi": "जैविक आलू", "variety": "Indian", "base_price": (18, 30), "unit": "kg"},
        {"name_en": "Red Onions", "name_hi": "लाल प्याज", "variety": "Nashik", "base_price": (30, 55), "unit": "kg"},
        {"name_en": "Green Cabbage", "name_hi": "हरी पत्तागोभी", "variety": "Fresh", "base_price": (20, 35), "unit": "kg"},
        {"name_en": "Cauliflower", "name_hi": "फूलगोभी", "variety": "White", "base_price": (25, 45), "unit": "kg"},
        {"name_en": "Fresh Carrots", "name_hi": "ताज़ी गाजर", "variety": "Orange", "base_price": (35, 55), "unit": "kg"},
        {"name_en": "Baby Spinach", "name_hi": "पालक", "variety": "Organic", "base_price": (25, 40), "unit": "kg"},
        {"name_en": "Purple Brinjal", "name_hi": "बैंगन", "variety": "Long", "base_price": (30, 45), "unit": "kg"},
        {"name_en": "Green Lady Finger", "name_hi": "भिंडी", "variety": "Fresh", "base_price": (35, 55), "unit": "kg"},
        {"name_en": "Green Capsicum", "name_hi": "शिमला मिर्च", "variety": "Bell Pepper", "base_price": (45, 70), "unit": "kg"},
        {"name_en": "Fresh Green Peas", "name_hi": "हरी मटर", "variety": "Sweet", "base_price": (60, 90), "unit": "kg"},
        {"name_en": "Drumsticks", "name_hi": "सहजन", "variety": "Fresh", "base_price": (40, 60), "unit": "kg"},
    ],
    "fruits": [
        {"name_en": "Alphonso Mangoes", "name_hi": "हापुस आम", "variety": "Alphonso", "base_price": (180, 300), "unit": "kg"},
        {"name_en": "Fresh Bananas", "name_hi": "केले", "variety": "Robusta", "base_price": (35, 55), "unit": "dozen"},
        {"name_en": "Shimla Apples", "name_hi": "शिमला सेब", "variety": "Royal Gala", "base_price": (100, 160), "unit": "kg"},
        {"name_en": "Nagpur Oranges", "name_hi": "नागपुर संतरे", "variety": "Sweet", "base_price": (60, 100), "unit": "kg"},
        {"name_en": "Green Grapes", "name_hi": "हरे अंगूर", "variety": "Thompson", "base_price": (50, 90), "unit": "kg"},
        {"name_en": "Fresh Watermelon", "name_hi": "तरबूज", "variety": "Red", "base_price": (15, 30), "unit": "kg"},
        {"name_en": "Ruby Pomegranate", "name_hi": "अनार", "variety": "Bhagwa", "base_price": (120, 200), "unit": "kg"},
        {"name_en": "Sweet Papaya", "name_hi": "पपीता", "variety": "Red Lady", "base_price": (25, 45), "unit": "kg"},
        {"name_en": "Guava", "name_hi": "अमरूद", "variety": "Allahabad", "base_price": (35, 55), "unit": "kg"},
        {"name_en": "Chikoo", "name_hi": "चीकू", "variety": "Kalipatti", "base_price": (45, 70), "unit": "kg"},
    ],
    "grains": [
        {"name_en": "Basmati Rice", "name_hi": "बासमती चावल", "variety": "1121", "base_price": (70, 120), "unit": "kg"},
        {"name_en": "Sharbati Wheat", "name_hi": "शरबती गेहूं", "variety": "Premium", "base_price": (30, 50), "unit": "kg"},
        {"name_en": "Yellow Maize", "name_hi": "पीली मक्का", "variety": "Hybrid", "base_price": (22, 38), "unit": "kg"},
        {"name_en": "Pearl Millet", "name_hi": "बाजरा", "variety": "Desi", "base_price": (35, 55), "unit": "kg"},
        {"name_en": "Jowar", "name_hi": "ज्वार", "variety": "White", "base_price": (40, 60), "unit": "kg"},
        {"name_en": "Finger Millet", "name_hi": "रागी", "variety": "Organic", "base_price": (45, 70), "unit": "kg"},
        {"name_en": "Brown Rice", "name_hi": "ब्राउन चावल", "variety": "Organic", "base_price": (80, 130), "unit": "kg"},
        {"name_en": "Quinoa", "name_hi": "क्विनोआ", "variety": "White", "base_price": (250, 400), "unit": "kg"},
    ],
    "spices": [
        {"name_en": "Turmeric Powder", "name_hi": "हल्दी पाउडर", "variety": "Salem", "base_price": (120, 200), "unit": "kg"},
        {"name_en": "Red Chili Powder", "name_hi": "लाल मिर्च पाउडर", "variety": "Kashmiri", "base_price": (180, 280), "unit": "kg"},
        {"name_en": "Coriander Powder", "name_hi": "धनिया पाउडर", "variety": "Ground", "base_price": (100, 160), "unit": "kg"},
        {"name_en": "Cumin Seeds", "name_hi": "जीरा", "variety": "Rajasthan", "base_price": (280, 400), "unit": "kg"},
        {"name_en": "Black Pepper", "name_hi": "काली मिर्च", "variety": "Malabar", "base_price": (450, 700), "unit": "kg"},
        {"name_en": "Green Cardamom", "name_hi": "हरी इलायची", "variety": "Premium", "base_price": (1100, 1700), "unit": "kg"},
        {"name_en": "Cinnamon Sticks", "name_hi": "दालचीनी", "variety": "Ceylon", "base_price": (350, 550), "unit": "kg"},
        {"name_en": "Whole Cloves", "name_hi": "लौंग", "variety": "Handpicked", "base_price": (700, 1100), "unit": "kg"},
    ],
    "dairy": [
        {"name_en": "Farm Fresh Milk", "name_hi": "ताज़ा दूध", "variety": "Full Cream", "base_price": (55, 75), "unit": "liter"},
        {"name_en": "Desi Ghee", "name_hi": "देसी घी", "variety": "Pure", "base_price": (500, 750), "unit": "kg"},
        {"name_en": "Paneer", "name_hi": "पनीर", "variety": "Fresh", "base_price": (350, 450), "unit": "kg"},
        {"name_en": "Curd", "name_hi": "दही", "variety": "Thick", "base_price": (50, 70), "unit": "kg"},
        {"name_en": "Butter", "name_hi": "मक्खन", "variety": "Unsalted", "base_price": (450, 600), "unit": "kg"},
    ]
}

QUALITY_GRADES = ["premium", "grade_a", "grade_b", "standard", "organic"]
DESCRIPTIONS_EN = [
    "Premium quality {product} sourced directly from local farms. Fresh and hygienically packed.",
    "Farm-fresh {product} with no preservatives. Ideal for daily cooking needs.",
    "High-grade {product} carefully selected for superior taste and quality.",
    "Organic {product} grown without pesticides. Perfect for health-conscious buyers.",
    "Freshly harvested {product} available in bulk. Best prices guaranteed."
]
DESCRIPTIONS_HI = [
    "स्थानीय खेतों से सीधे प्राप्त प्रीमियम गुणवत्ता वाला {product}। ताज़ा और स्वच्छ रूप से पैक।",
    "बिना परिरक्षकों के खेत से ताज़ा {product}। दैनिक खाना पकाने की जरूरतों के लिए आदर्श।",
    "बेहतर स्वाद और गुणवत्ता के लिए सावधानीपूर्वक चयनित उच्च श्रेणी का {product}।",
    "कीटनाशकों के बिना उगाया गया जैविक {product}। स्वास्थ्य के प्रति जागरूक खरीदारों के लिए उपयुक्त।",
    "ताज़ी फसल {product} थोक में उपलब्ध। सर्वोत्तम मूल्य की गारंटी।"
]


async def clear_database(db):
    """Clear all existing data."""
    print("Clearing existing data...")
    await db.users.delete_many({})
    await db.products.delete_many({})
    await db.conversations.delete_many({})
    await db.messages.delete_many({})
    await db.transactions.delete_many({})
    await db.market_prices.delete_many({})
    print("✓ Database cleared")


async def create_vendors(db):
    """Create vendor accounts with proper structure."""
    print("Creating vendor accounts...")
    vendors = []
    
    for i, v in enumerate(VENDOR_DATA, 1):
        user_id = str(ObjectId())
        
        vendor = {
            "user_id": user_id,
            "email": f"vendor{i}@mandi.example.com",
            "phone": f"+91{9000000000 + i}",
            "password_hash": pwd_context.hash("password123"),
            "role": "vendor",
            "preferred_languages": ["en", "hi"],
            "location": {
                "address": f"{v['city']} Market Area",
                "city": v["city"],
                "state": v["state"],
                "pincode": v["pincode"],
                "country": "India",
                "coordinates": [v["lon"], v["lat"]]  # GeoJSON: [lon, lat]
            },
            "verification_status": "verified",
            "preferences": {
                "preferred_languages": ["en", "hi"],
                "notification_settings": {
                    "email_notifications": True,
                    "sms_notifications": True,
                    "push_notifications": True,
                    "marketing_emails": False
                },
                "privacy_settings": {
                    "show_phone": True,
                    "show_location": True,
                    "allow_direct_contact": True
                },
                "accessibility_settings": {
                    "high_contrast": False,
                    "large_text": False,
                    "voice_navigation": False,
                    "screen_reader": False
                }
            },
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=random.randint(30, 180)),
            "updated_at": datetime.utcnow(),
            "last_login": datetime.utcnow() - timedelta(days=random.randint(0, 7)),
            
            # Vendor-specific fields
            "business_name": v["business"],
            "business_type": random.choice(["individual", "small_business", "cooperative", "wholesaler"]),
            "product_categories": v["categories"],
            "market_location": f"{v['city']} Main Mandi",
            "verification_documents": [],
            "rating": round(random.uniform(3.5, 5.0), 1),
            "total_transactions": random.randint(10, 200),
            "total_revenue": str(random.randint(50000, 500000))
        }
        
        vendors.append(vendor)
    
    await db.users.insert_many(vendors)
    print(f"✓ Created {len(vendors)} vendor accounts")
    return vendors


async def create_buyers(db):
    """Create buyer accounts with proper structure."""
    print("Creating buyer accounts...")
    buyers = []
    
    for i, b in enumerate(BUYER_DATA, 1):
        user_id = str(ObjectId())
        
        buyer = {
            "user_id": user_id,
            "email": f"buyer{i}@mandi.example.com",
            "phone": f"+91{8000000000 + i}",
            "password_hash": pwd_context.hash("password123"),
            "role": "buyer",
            "preferred_languages": ["en", "hi"],
            "location": {
                "address": f"{b['city']} Residential Area",
                "city": b["city"],
                "state": b["state"],
                "pincode": b["pincode"],
                "country": "India",
                "coordinates": [b["lon"], b["lat"]]
            },
            "verification_status": "verified",
            "preferences": {
                "preferred_languages": ["en", "hi"],
                "notification_settings": {
                    "email_notifications": True,
                    "sms_notifications": True,
                    "push_notifications": True,
                    "marketing_emails": False
                },
                "privacy_settings": {
                    "show_phone": False,
                    "show_location": True,
                    "allow_direct_contact": True
                },
                "accessibility_settings": {
                    "high_contrast": False,
                    "large_text": False,
                    "voice_navigation": False,
                    "screen_reader": False
                }
            },
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=random.randint(10, 90)),
            "updated_at": datetime.utcnow(),
            "last_login": datetime.utcnow() - timedelta(days=random.randint(0, 5)),
            
            # Buyer-specific fields
            "purchase_history": [],
            "preferred_categories": random.sample(list(PRODUCT_TEMPLATES.keys()), k=random.randint(2, 4)),
            "budget_range": {
                "min_amount": str(random.randint(500, 2000)),
                "max_amount": str(random.randint(5000, 20000)),
                "currency": "INR"
            },
            "delivery_addresses": [],
            "total_purchases": random.randint(0, 50),
            "total_spent": str(random.randint(0, 100000))
        }
        
        buyers.append(buyer)
    
    await db.users.insert_many(buyers)
    print(f"✓ Created {len(buyers)} buyer accounts")
    return buyers


async def create_products(db, vendors):
    """Create products with proper structure matching the backend models."""
    print("Creating products...")
    products = []
    
    for category, templates in PRODUCT_TEMPLATES.items():
        # Find vendors that sell this category
        category_vendors = [v for v in vendors if category in v["product_categories"]]
        if not category_vendors:
            category_vendors = vendors  # Fallback to all vendors
        
        for template in templates:
            # Create 1-2 products per template
            num_products = random.randint(1, 2)
            
            for _ in range(num_products):
                vendor = random.choice(category_vendors)
                product_id = str(ObjectId())
                
                min_price, max_price = template["base_price"]
                price = round(random.uniform(min_price, max_price), 2)
                
                # Select description templates
                desc_idx = random.randint(0, len(DESCRIPTIONS_EN) - 1)
                desc_en = DESCRIPTIONS_EN[desc_idx].format(product=template["name_en"])
                desc_hi = DESCRIPTIONS_HI[desc_idx].format(product=template["name_hi"])
                
                quality = random.choice(QUALITY_GRADES)
                
                product = {
                    "product_id": product_id,
                    "vendor_id": vendor["user_id"],
                    
                    # Multilingual name
                    "name": {
                        "original_language": "en",
                        "original_text": template["name_en"],
                        "translations": {
                            "en": template["name_en"],
                            "hi": template["name_hi"]
                        },
                        "auto_translated": False,
                        "last_updated": datetime.utcnow().isoformat()
                    },
                    
                    # Multilingual description
                    "description": {
                        "original_language": "en",
                        "original_text": desc_en,
                        "translations": {
                            "en": desc_en,
                            "hi": desc_hi
                        },
                        "auto_translated": False,
                        "last_updated": datetime.utcnow().isoformat()
                    },
                    
                    "category": category,
                    "subcategory": template.get("variety", "Standard"),
                    "tags": [category, template["variety"].lower(), "fresh", "local"],
                    
                    # Images
                    "images": [{
                        "image_id": str(ObjectId()),
                        "image_url": f"https://placehold.co/600x400/png?text={template['name_en'].replace(' ', '+')}",
                        "thumbnail_url": f"https://placehold.co/200x200/png?text={template['name_en'].replace(' ', '+')}",
                        "alt_text": template["name_en"],
                        "is_primary": True,
                        "uploaded_at": datetime.utcnow().isoformat(),
                        "file_size": 50000,
                        "dimensions": {"width": 600, "height": 400}
                    }],
                    
                    # Price info
                    "price_info": {
                        "base_price": str(price),
                        "currency": "INR",
                        "negotiable": random.choice([True, False]),
                        "bulk_discount": None,
                        "seasonal_pricing": None
                    },
                    
                    # Availability
                    "availability": {
                        "quantity_available": random.randint(50, 500),
                        "unit": template["unit"],
                        "minimum_order": random.choice([1, 5, 10]),
                        "maximum_order": random.randint(50, 200),
                        "available_from": datetime.utcnow().isoformat(),
                        "available_until": None,
                        "restocking_date": None
                    },
                    
                    # Location (same as vendor)
                    "location": {
                        "address": vendor["location"]["address"],
                        "city": vendor["location"]["city"],
                        "state": vendor["location"]["state"],
                        "pincode": vendor["location"]["pincode"],
                        "country": "India",
                        "coordinates": vendor["location"]["coordinates"],
                        "market_name": vendor["market_location"]
                    },
                    
                    "quality_grade": quality,
                    
                    # Metadata
                    "metadata": {
                        "harvest_date": (datetime.utcnow() - timedelta(days=random.randint(1, 7))).date().isoformat(),
                        "expiry_date": (datetime.utcnow() + timedelta(days=random.randint(7, 30))).date().isoformat() if category != "grains" else None,
                        "storage_conditions": "Cool and dry place" if category in ["grains", "spices"] else "Refrigerate at 4°C",
                        "certifications": ["organic"] if quality == "organic" else [],
                        "origin": vendor["location"]["state"],
                        "variety": template.get("variety"),
                        "processing_method": None
                    },
                    
                    "status": "active",
                    "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    "updated_at": datetime.utcnow(),
                    "views_count": random.randint(10, 500),
                    "favorites_count": random.randint(0, 50),
                    "search_keywords": [
                        template["name_en"].lower(),
                        template["name_hi"],
                        category,
                        template.get("variety", "").lower(),
                        "fresh"
                    ],
                    "featured": random.random() < 0.1  # 10% chance of being featured
                }
                
                products.append(product)
    
    await db.products.insert_many(products)
    print(f"✓ Created {len(products)} products across {len(PRODUCT_TEMPLATES)} categories")
    return products


async def create_indexes(db):
    """Create database indexes."""
    print("Creating database indexes...")
    
    try:
        # Drop existing text indexes first to avoid conflicts
        try:
            await db.products.drop_index("product_text_search")
        except:
            pass
        try:
            await db.products.drop_index("name.original_text_text_description.original_text_text")
        except:
            pass
        
        # User indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index([("phone", 1)], unique=True, sparse=True)
        await db.users.create_index("role")
        await db.users.create_index([("location.coordinates", "2dsphere")])
        
        # Product indexes
        await db.products.create_index("product_id", unique=True)
        await db.products.create_index("vendor_id")
        await db.products.create_index("category")
        await db.products.create_index("status")
        await db.products.create_index([("location.coordinates", "2dsphere")])
        await db.products.create_index([("created_at", -1)])
        
        # Create text search index for products
        await db.products.create_index(
            [
                ("name.original_text", "text"),
                ("description.original_text", "text"),
                ("name.translations.hi", "text"),
                ("name.translations.en", "text"),
                ("tags", "text"),
                ("metadata.variety", "text"),
                ("metadata.origin", "text")
            ],
            name="product_text_search",
            default_language="english"
        )
        
        print("✓ Database indexes created")
    except Exception as e:
        print(f"⚠ Index creation warning (may be normal): {e}")


async def main():
    """Main seed function."""
    print("=" * 60)
    print("MULTILINGUAL MANDI MARKETPLACE - DATABASE SEEDING")
    print("=" * 60)
    print()
    
    # Connect to MongoDB
    print(f"Connecting to MongoDB at {MONGODB_URL}...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    try:
        # Test connection
        await client.admin.command('ping')
        print("✓ Connected to MongoDB successfully")
        print()
        
        # Clear existing data
        await clear_database(db)
        print()
        
        # Create indexes
        await create_indexes(db)
        print()
        
        # Create vendors
        vendors = await create_vendors(db)
        print()
        
        # Create buyers
        buyers = await create_buyers(db)
        print()
        
        # Create products
        products = await create_products(db, vendors)
        print()
        
        # Summary
        print("=" * 60)
        print("SEEDING COMPLETE!")
        print("=" * 60)
        print(f"Total Vendors: {len(vendors)}")
        print(f"Total Buyers: {len(buyers)}")
        print(f"Total Products: {len(products)}")
        print()
        print("Sample Login Credentials:")
        print("-" * 60)
        print("Vendor Account:")
        print("  Email: vendor1@mandi.example.com")
        print("  Password: password123")
        print()
        print("Buyer Account:")
        print("  Email: buyer1@mandi.example.com")
        print("  Password: password123")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        client.close()
        print()
        print("Database connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
