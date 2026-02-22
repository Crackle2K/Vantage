import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.mongodb import connect_to_mongo, get_businesses_collection

async def main():
    await connect_to_mongo()
    c = get_businesses_collection()
    await c.create_index([("location", "2dsphere")])
    print("2dsphere index created")
    idxs = await c.index_information()
    for k in idxs:
        print(f"  {k}")

asyncio.run(main())
