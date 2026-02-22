"""
MongoDB Connection Module
Provides async database connection using Motor driver
"""

from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_URI, DATABASE_NAME

# Global database client
client: AsyncIOMotorClient = None
database = None


async def connect_to_mongo():
    """
    Establish connection to MongoDB Atlas
    Called on application startup
    """
    global client, database
    try:
        client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        database = client[DATABASE_NAME]
        
        # Test connection
        await client.admin.command('ping')
        print(f"✅ Connected to MongoDB: {DATABASE_NAME}")

        # Ensure indexes
        await _ensure_indexes()
    except Exception as e:
        print(f"⚠️  MongoDB connection warning: {e}")
        print("⚠️  Server will start without database. Some features may not work.")
        print("   To fix: Install MongoDB or configure MongoDB Atlas connection string")


async def _ensure_indexes():
    """Create required indexes if they don't already exist."""
    try:
        businesses = get_businesses_collection()
        await businesses.create_index([("location", "2dsphere")])
        await businesses.create_index("place_id", unique=True, sparse=True)
        await businesses.create_index("category")
        await businesses.create_index("owner_id", sparse=True)
        await businesses.create_index("live_visibility_score")

        visits = get_visits_collection()
        await visits.create_index([("user_id", 1), ("business_id", 1), ("created_at", -1)])
        await visits.create_index("business_id")

        geo_cache = get_geo_cache_collection()
        await geo_cache.create_index([("cell_lat", 1), ("cell_lng", 1), ("radius_bucket", 1)], unique=True)
        await geo_cache.create_index("fetched_at")

        api_log = get_api_usage_log_collection()
        await api_log.create_index("timestamp")

        print("✅ MongoDB indexes ensured")
    except Exception as e:
        print(f"⚠️  Index creation warning: {e}")


async def close_mongo_connection():
    """
    Close MongoDB connection
    Called on application shutdown
    """
    global client
    if client:
        client.close()
        print("🔌 MongoDB connection closed")


def get_database():
    """
    Get the database instance
    Returns the active database connection
    """
    if database is None:
        raise Exception("Database not initialized. Call connect_to_mongo() first.")
    return database


# Collection getters for easy access
def get_users_collection():
    """Get users collection"""
    return get_database()["users"]


def get_businesses_collection():
    """Get businesses collection"""
    return get_database()["businesses"]


def get_reviews_collection():
    """Get reviews collection"""
    return get_database()["reviews"]


def get_deals_collection():
    """Get deals collection"""
    return get_database()["deals"]


def get_claims_collection():
    """Get business claims collection"""
    return get_database()["claims"]


def get_checkins_collection():
    """Get check-ins collection"""
    return get_database()["checkins"]


def get_activity_feed_collection():
    """Get activity feed collection"""
    return get_database()["activity_feed"]


def get_credibility_collection():
    """Get user credibility scores collection"""
    return get_database()["credibility"]


def get_subscriptions_collection():
    """Get subscriptions collection"""
    return get_database()["subscriptions"]


def get_visits_collection():
    """Get verified visits collection"""
    return get_database()["visits"]


def get_geo_cache_collection():
<<<<<<< Updated upstream
    """Get geo-cache collection (tracks which areas have been fetched from Google)"""
=======
    """Get geo-area cache — tracks which lat/lng cells we already fetched from Google"""
>>>>>>> Stashed changes
    return get_database()["geo_cache"]


def get_api_usage_log_collection():
<<<<<<< Updated upstream
    """Get API usage log collection (audits every Google API call)"""
=======
    """Get API usage log — every outbound Google Places call is recorded here"""
>>>>>>> Stashed changes
    return get_database()["api_usage_log"]
