"""
Database Initialization Script
Creates necessary indexes and seeds sample data for Vantage
"""

import asyncio
from datetime import datetime, timedelta
from database.mongodb import connect_to_mongo, get_businesses_collection, get_reviews_collection, get_deals_collection, get_users_collection


SAMPLE_BUSINESSES = [
    {
        "name": "The Green Bean Café",
        "category": "food",
        "description": "A cozy neighborhood café serving organic coffee, fresh pastries, and farm-to-table breakfast bowls. Perfect for remote work or catching up with friends.",
        "address": "142 Main Street",
        "city": "Toronto",
        "location": {"type": "Point", "coordinates": [-79.3832, 43.6532]},
        "phone": "(416) 555-0101",
        "email": "hello@greenbean.ca",
        "website": "https://greenbean.ca",
        "image_url": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=600",
        "rating_average": 4.6,
        "total_reviews": 128,
        "has_deals": True,
        "created_at": datetime.utcnow() - timedelta(days=120),
    },
    {
        "name": "Urban Threads Boutique",
        "category": "retail",
        "description": "Curated fashion for the modern urbanite. We carry local designers and sustainable brands you won't find anywhere else.",
        "address": "88 Queen Street West",
        "city": "Toronto",
        "location": {"type": "Point", "coordinates": [-79.3871, 43.6515]},
        "phone": "(416) 555-0202",
        "email": "shop@urbanthreads.ca",
        "website": "https://urbanthreads.ca",
        "image_url": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=600",
        "rating_average": 4.3,
        "total_reviews": 67,
        "has_deals": False,
        "created_at": datetime.utcnow() - timedelta(days=90),
    },
    {
        "name": "FitZone Studio",
        "category": "health",
        "description": "High-energy group fitness classes including HIIT, yoga, spin, and strength training. First class free for new members!",
        "address": "200 King Street East",
        "city": "Toronto",
        "location": {"type": "Point", "coordinates": [-79.3700, 43.6510]},
        "phone": "(416) 555-0303",
        "email": "info@fitzone.ca",
        "website": "https://fitzone.ca",
        "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=600",
        "rating_average": 4.8,
        "total_reviews": 215,
        "has_deals": True,
        "created_at": datetime.utcnow() - timedelta(days=200),
    },
    {
        "name": "Pixel Perfect Repairs",
        "category": "services",
        "description": "Expert phone, tablet, and laptop repair. Same-day screen replacements and data recovery. Trusted by thousands since 2018.",
        "address": "55 Dundas Street West",
        "city": "Toronto",
        "location": {"type": "Point", "coordinates": [-79.3818, 43.6555]},
        "phone": "(416) 555-0404",
        "email": "fix@pixelperfect.ca",
        "image_url": "https://images.unsplash.com/photo-1581092918056-0c4c3acd3789?w=600",
        "rating_average": 4.1,
        "total_reviews": 89,
        "has_deals": False,
        "created_at": datetime.utcnow() - timedelta(days=150),
    },
    {
        "name": "Laugh Factory Toronto",
        "category": "entertainment",
        "description": "Live stand-up comedy every night! Open mic on Tuesdays, headliner shows on weekends. Full bar and appetizer menu.",
        "address": "370 King Street West",
        "city": "Toronto",
        "location": {"type": "Point", "coordinates": [-79.3928, 43.6445]},
        "phone": "(416) 555-0505",
        "email": "tickets@laughfactoryto.ca",
        "website": "https://laughfactoryto.ca",
        "image_url": "https://images.unsplash.com/photo-1585699324551-f6c309eedeca?w=600",
        "rating_average": 4.5,
        "total_reviews": 312,
        "has_deals": True,
        "created_at": datetime.utcnow() - timedelta(days=300),
    },
    {
        "name": "Sakura Ramen House",
        "category": "food",
        "description": "Authentic Japanese ramen with rich tonkotsu broth simmered for 18 hours. Handmade noodles daily. Vegetarian options available.",
        "address": "22 Baldwin Street",
        "city": "Toronto",
        "location": {"type": "Point", "coordinates": [-79.3920, 43.6560]},
        "phone": "(416) 555-0606",
        "email": "eat@sakuraramen.ca",
        "image_url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=600",
        "rating_average": 4.7,
        "total_reviews": 198,
        "has_deals": False,
        "created_at": datetime.utcnow() - timedelta(days=180),
    },
    {
        "name": "Glow Beauty Bar",
        "category": "health",
        "description": "Premium skincare treatments, facials, and beauty services. Our estheticians use only clean, cruelty-free products.",
        "address": "156 Bloor Street West",
        "city": "Toronto",
        "location": {"type": "Point", "coordinates": [-79.3900, 43.6677]},
        "phone": "(416) 555-0707",
        "email": "book@glowbeauty.ca",
        "website": "https://glowbeauty.ca",
        "image_url": "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=600",
        "rating_average": 4.4,
        "total_reviews": 156,
        "has_deals": True,
        "created_at": datetime.utcnow() - timedelta(days=100),
    },
    {
        "name": "BookNook Independent",
        "category": "retail",
        "description": "An independent bookstore with a carefully curated collection. Author readings every Saturday. Cozy reading nooks and a kids' corner.",
        "address": "78 Harbord Street",
        "city": "Toronto",
        "location": {"type": "Point", "coordinates": [-79.4010, 43.6620]},
        "phone": "(416) 555-0808",
        "email": "read@booknook.ca",
        "website": "https://booknook.ca",
        "image_url": "https://images.unsplash.com/photo-1526243741027-444d633d7365?w=600",
        "rating_average": 4.9,
        "total_reviews": 87,
        "has_deals": False,
        "created_at": datetime.utcnow() - timedelta(days=250),
    },
    {
        "name": "TechHub Coworking",
        "category": "services",
        "description": "Modern coworking space for freelancers and startups. High-speed WiFi, meeting rooms, and a rooftop terrace. Day passes available.",
        "address": "401 Richmond Street West",
        "city": "Toronto",
        "location": {"type": "Point", "coordinates": [-79.3950, 43.6490]},
        "phone": "(416) 555-0909",
        "email": "hello@techhub.ca",
        "website": "https://techhub.ca",
        "image_url": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=600",
        "rating_average": 4.2,
        "total_reviews": 45,
        "has_deals": True,
        "created_at": datetime.utcnow() - timedelta(days=60),
    },
    {
        "name": "Vinyl Vibes Records",
        "category": "entertainment",
        "description": "New and vintage vinyl records, turntables, and audio gear. In-store listening stations and live DJ sets on Fridays.",
        "address": "189 Ossington Avenue",
        "city": "Toronto",
        "location": {"type": "Point", "coordinates": [-79.4205, 43.6480]},
        "phone": "(416) 555-1010",
        "email": "spin@vinylvibes.ca",
        "image_url": "https://images.unsplash.com/photo-1483412033650-1015ddeb83d1?w=600",
        "rating_average": 4.6,
        "total_reviews": 73,
        "has_deals": False,
        "created_at": datetime.utcnow() - timedelta(days=170),
    },
    {
        "name": "Fresh Roots Market",
        "category": "food",
        "description": "Organic grocery and farmers market with locally sourced produce, artisan cheeses, and freshly baked bread daily.",
        "address": "310 Danforth Avenue",
        "city": "Toronto",
        "location": {"type": "Point", "coordinates": [-79.3500, 43.6790]},
        "phone": "(416) 555-1111",
        "email": "shop@freshroots.ca",
        "website": "https://freshroots.ca",
        "image_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=600",
        "rating_average": 4.5,
        "total_reviews": 142,
        "has_deals": True,
        "created_at": datetime.utcnow() - timedelta(days=80),
    },
    {
        "name": "Pawfect Pet Spa",
        "category": "services",
        "description": "Full-service pet grooming, daycare, and boarding. Your furry friend deserves the royal treatment. Certified pet first aid staff.",
        "address": "99 Roncesvalles Avenue",
        "city": "Toronto",
        "location": {"type": "Point", "coordinates": [-79.4490, 43.6450]},
        "phone": "(416) 555-1212",
        "email": "woof@pawfect.ca",
        "website": "https://pawfect.ca",
        "image_url": "https://images.unsplash.com/photo-1516734212186-a967f81ad0d7?w=600",
        "rating_average": 4.8,
        "total_reviews": 201,
        "has_deals": True,
        "created_at": datetime.utcnow() - timedelta(days=130),
    },
    {
        "name": "Summit Climbing Gym",
        "category": "health",
        "description": "Indoor rock climbing for all levels. Bouldering walls, top-rope routes, and a training area. Intro classes every weekend.",
        "address": "45 Fraser Avenue",
        "city": "Toronto",
        "location": {"type": "Point", "coordinates": [-79.4300, 43.6380]},
        "phone": "(416) 555-1313",
        "email": "climb@summitgym.ca",
        "website": "https://summitgym.ca",
        "image_url": "https://images.unsplash.com/photo-1522163182402-834f871fd851?w=600",
        "rating_average": 4.3,
        "total_reviews": 94,
        "has_deals": False,
        "created_at": datetime.utcnow() - timedelta(days=220),
    },
    {
        "name": "Nonna's Pizzeria",
        "category": "food",
        "description": "Wood-fired Neapolitan pizza made with imported Italian ingredients. Family recipes passed down for three generations.",
        "address": "234 College Street",
        "city": "Toronto",
        "location": {"type": "Point", "coordinates": [-79.4050, 43.6580]},
        "phone": "(416) 555-1414",
        "email": "eat@nonnas.ca",
        "image_url": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=600",
        "rating_average": 4.7,
        "total_reviews": 267,
        "has_deals": True,
        "created_at": datetime.utcnow() - timedelta(days=350),
    },
    {
        "name": "Spark Electronics",
        "category": "retail",
        "description": "Gadgets, components, and maker supplies. From Arduino kits to 3D printers. Staff are makers who can help with any project.",
        "address": "512 Spadina Avenue",
        "city": "Toronto",
        "location": {"type": "Point", "coordinates": [-79.4000, 43.6600]},
        "phone": "(416) 555-1515",
        "email": "hello@sparkelectronics.ca",
        "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=600",
        "rating_average": 4.0,
        "total_reviews": 38,
        "has_deals": False,
        "created_at": datetime.utcnow() - timedelta(days=45),
    },
]

SAMPLE_DEALS = [
    {
        "title": "20% Off All Lattes",
        "description": "Get 20% off any latte order this week. Show this deal at checkout!",
        "discount_percent": 20,
        "active": True,
    },
    {
        "title": "Free First Class",
        "description": "New members get their first group fitness class absolutely free. No commitment required.",
        "discount_percent": 100,
        "active": True,
    },
    {
        "title": "Comedy Night 2-for-1",
        "description": "Buy one ticket, get one free for any weeknight show. Valid Sunday through Thursday.",
        "discount_percent": 50,
        "active": True,
    },
    {
        "title": "15% Off Skincare Packages",
        "description": "Book any facial package and save 15%. Includes complimentary skin consultation.",
        "discount_percent": 15,
        "active": True,
    },
    {
        "title": "Free Day Pass",
        "description": "Try our coworking space free for one day. Includes WiFi, coffee, and meeting room access.",
        "discount_percent": 100,
        "active": True,
    },
    {
        "title": "10% Off Organic Produce",
        "description": "Save 10% on all organic fruits and vegetables every Wednesday.",
        "discount_percent": 10,
        "active": True,
    },
    {
        "title": "First Grooming 25% Off",
        "description": "New customers get 25% off their pet's first grooming session.",
        "discount_percent": 25,
        "active": True,
    },
    {
        "title": "Family Pizza Deal",
        "description": "Buy 2 large pizzas and get a free appetizer. Dine-in or takeout.",
        "discount_percent": 15,
        "active": True,
    },
]


async def create_indexes():
    """Create all necessary database indexes"""
    await connect_to_mongo()
    
    print("Creating database indexes...")
    
    # Users collection indexes
    users_collection = get_users_collection()
    await users_collection.create_index("email", unique=True)
    print("✅ Users indexes created")
    
    # Businesses collection indexes
    businesses_collection = get_businesses_collection()
    await businesses_collection.create_index([("location", "2dsphere")])
    await businesses_collection.create_index("owner_id")
    await businesses_collection.create_index("category")
    await businesses_collection.create_index("city")
    print("✅ Businesses indexes created (including geospatial index)")
    
    # Reviews collection indexes
    reviews_collection = get_reviews_collection()
    await reviews_collection.create_index([("user_id", 1), ("business_id", 1)], unique=True)
    await reviews_collection.create_index("business_id")
    await reviews_collection.create_index("user_id")
    await reviews_collection.create_index("created_at")
    print("✅ Reviews indexes created (including unique constraint)")
    
    # Deals collection indexes
    deals_collection = get_deals_collection()
    await deals_collection.create_index("business_id")
    await deals_collection.create_index("active")
    await deals_collection.create_index([("active", 1), ("expires_at", 1)])
    await deals_collection.create_index("expires_at")
    print("✅ Deals indexes created")
    
    print("\n🎉 All indexes created successfully!")


async def seed_data():
    """Seed the database with sample businesses and deals if empty"""
    await connect_to_mongo()

    businesses_collection = get_businesses_collection()
    deals_collection = get_deals_collection()

    count = await businesses_collection.count_documents({})
    if count > 0:
        print(f"ℹ️  Database already has {count} businesses. Skipping seed.")
        return

    print("🌱 Seeding sample businesses...")
    result = await businesses_collection.insert_many(SAMPLE_BUSINESSES)
    inserted_ids = result.inserted_ids
    print(f"   Inserted {len(inserted_ids)} businesses")

    # Attach deals to businesses that have has_deals=True
    deal_businesses = [
        (i, b) for i, b in enumerate(SAMPLE_BUSINESSES) if b.get("has_deals")
    ]
    deals_to_insert = []
    for deal_idx, (biz_idx, _biz) in enumerate(deal_businesses):
        if deal_idx < len(SAMPLE_DEALS):
            deal = {
                **SAMPLE_DEALS[deal_idx],
                "business_id": str(inserted_ids[biz_idx]),
                "expires_at": datetime.utcnow() + timedelta(days=30),
                "created_at": datetime.utcnow(),
            }
            deals_to_insert.append(deal)

    if deals_to_insert:
        await deals_collection.insert_many(deals_to_insert)
        print(f"   Inserted {len(deals_to_insert)} deals")

    print("🎉 Seed data loaded successfully!")


async def init_all():
    """Run indexes + seed"""
    await create_indexes()
    await seed_data()


if __name__ == "__main__":
    asyncio.run(init_all())
