import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_db():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['mandi_marketplace']
    
    user = await db.users.find_one({'email': 'vendor1@mandi.local'})
    if user:
        user_id = user.get('user_id')
        print(f"_id: {user.get('_id')}")
        print(f"user_id: {user_id}")
        print(f"email: {user.get('email')}")
        
        # Test query by user_id
        print(f"\nTesting query by user_id: {user_id}")
        found = await db.users.find_one({'user_id': user_id})
        if found:
            print(f"SUCCESS: Found user by user_id!")
            print(f"  Email: {found.get('email')}")
        else:
            print("FAILED: Could not find user by user_id")
    else:
        print('User not found in database')
    
    client.close()

asyncio.run(check_db())
