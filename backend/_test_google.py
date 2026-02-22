import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.mongodb import connect_to_mongo, get_businesses_collection
from services.google_places import search_google_places

async def test():
    await connect_to_mongo()
    coll = get_businesses_collection()

    print("Testing Google Places API...")
    results = await search_google_places(43.6532, -79.3832, 5000)
    print(f"Google returned {len(results)} businesses")

    if results:
        inserted = 0
        for place in results:
            exists = await coll.find_one({"place_id": place["place_id"]})
            if not exists:
                await coll.insert_one(place)
                inserted += 1
        print(f"Inserted {inserted} new businesses into MongoDB")

        total = await coll.count_documents({})
        print(f"Total businesses now: {total}")

        cursor = coll.find().limit(5)
        async for doc in cursor:
            name = doc.get("name", "?")
            cat = doc.get("category", "?")
            pid = str(doc.get("place_id", "NONE"))[:25]
            print(f"  - {name} ({cat}) pid={pid}")
    else:
        print("No results from Google - check API key!")

asyncio.run(test())
