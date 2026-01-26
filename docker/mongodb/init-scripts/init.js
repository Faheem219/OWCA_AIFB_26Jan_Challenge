// MongoDB initialization script for Mandi Marketplace
// This script creates the initial database structure and indexes

// Switch to the mandi_marketplace database
db = db.getSiblingDB('mandi_marketplace');

// Create collections with validation schemas
db.createCollection('users', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['email', 'role', 'preferred_languages', 'created_at'],
            properties: {
                email: {
                    bsonType: 'string',
                    pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
                },
                role: {
                    bsonType: 'string',
                    enum: ['VENDOR', 'BUYER']
                },
                preferred_languages: {
                    bsonType: 'array',
                    items: {
                        bsonType: 'string',
                        enum: ['hi', 'en', 'ta', 'te', 'kn', 'ml', 'gu', 'pa', 'bn', 'mr']
                    }
                },
                created_at: {
                    bsonType: 'date'
                }
            }
        }
    }
});

db.createCollection('products', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['vendor_id', 'name', 'category', 'base_price', 'created_at'],
            properties: {
                vendor_id: {
                    bsonType: 'objectId'
                },
                name: {
                    bsonType: 'object',
                    required: ['original_language', 'original_text'],
                    properties: {
                        original_language: {
                            bsonType: 'string'
                        },
                        original_text: {
                            bsonType: 'string'
                        },
                        translations: {
                            bsonType: 'object'
                        }
                    }
                },
                category: {
                    bsonType: 'string',
                    enum: ['VEGETABLES', 'FRUITS', 'GRAINS', 'SPICES', 'DAIRY']
                },
                base_price: {
                    bsonType: 'decimal'
                },
                created_at: {
                    bsonType: 'date'
                }
            }
        }
    }
});

db.createCollection('conversations');
db.createCollection('messages');
db.createCollection('transactions');
db.createCollection('market_prices');

// Create indexes for performance
// User indexes
db.users.createIndex({ 'email': 1 }, { unique: true });
db.users.createIndex({ 'phone': 1 }, { sparse: true, unique: true });
db.users.createIndex({ 'role': 1 });
db.users.createIndex({ 'location.coordinates': '2dsphere' });

// Product indexes
db.products.createIndex({ 'vendor_id': 1 });
db.products.createIndex({ 'category': 1 });
db.products.createIndex({ 'status': 1 });
db.products.createIndex({ 'location.coordinates': '2dsphere' });
db.products.createIndex({ 'name.original_text': 'text', 'description.original_text': 'text' });
db.products.createIndex({ 'base_price': 1 });
db.products.createIndex({ 'created_at': -1 });

// Conversation and message indexes
db.conversations.createIndex({ 'participants': 1 });
db.conversations.createIndex({ 'last_activity': -1 });
db.messages.createIndex({ 'conversation_id': 1, 'timestamp': -1 });
db.messages.createIndex({ 'sender_id': 1 });

// Transaction indexes
db.transactions.createIndex({ 'buyer_id': 1 });
db.transactions.createIndex({ 'vendor_id': 1 });
db.transactions.createIndex({ 'product_id': 1 });
db.transactions.createIndex({ 'created_at': -1 });
db.transactions.createIndex({ 'payment_status': 1 });

// Market price indexes
db.market_prices.createIndex({ 'commodity': 1, 'market': 1, 'date': -1 });
db.market_prices.createIndex({ 'date': -1 });

print('MongoDB initialization completed successfully');
print('Created collections: users, products, conversations, messages, transactions, market_prices');
print('Created indexes for optimal query performance');