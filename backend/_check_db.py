import asyncio
from database.mongodb import connect_to_mongo, get_businesses_collection

async def check():
    await connect_to_mongo()
    coll = get_businesses_collection()
    count = await coll.count_documents({})
    print(f"Total businesses in DB: {count}")
    sample = await coll.find_one()
    if sample:
        name = sample.get("name", "?")
        has_loc = "location" in sample
        pid = sample.get("place_id", "NONE")
        print(f"Sample: name={name}, has_location={has_loc}, place_id={pid}")
        if has_loc:
            print(f"  location: {sample['location']}")
    else:
        print("No businesses found in database!")

asyncio.run(check())
