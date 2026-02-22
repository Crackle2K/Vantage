"""
Google Places Nearby Search integration.

• Maps Google place types → Vantage categories.
• Returns MongoDB-ready dicts with place_id, GeoJSON location, etc.
• Every API call is logged to the api_usage_log collection.
• Contains geo_cell_key() helper for geo-cache cell computation.
"""

import math
from datetime import datetime
from typing import List, Dict, Optional

import httpx

from config import GOOGLE_API_KEY
from database.mongodb import get_api_usage_log_collection

# ── Google type → Vantage category mapping ──────────────────────────
_TYPE_MAP = {
    "restaurant": "Restaurants",
    "food": "Restaurants",
    "meal_delivery": "Restaurants",
    "meal_takeaway": "Restaurants",
    "cafe": "Cafes & Coffee",
    "bakery": "Cafes & Coffee",
    "bar": "Bars & Nightlife",
    "night_club": "Bars & Nightlife",
    "clothing_store": "Shopping",
    "shoe_store": "Shopping",
    "shopping_mall": "Shopping",
    "store": "Shopping",
    "department_store": "Shopping",
    "home_goods_store": "Shopping",
    "furniture_store": "Shopping",
    "electronics_store": "Shopping",
    "book_store": "Shopping",
    "jewelry_store": "Shopping",
    "gym": "Fitness & Wellness",
    "spa": "Fitness & Wellness",
    "beauty_salon": "Beauty & Spas",
    "hair_care": "Beauty & Spas",
    "doctor": "Health & Medical",
    "dentist": "Health & Medical",
    "hospital": "Health & Medical",
    "pharmacy": "Health & Medical",
    "veterinary_care": "Health & Medical",
    "physiotherapist": "Health & Medical",
    "bank": "Financial Services",
    "accounting": "Financial Services",
    "insurance_agency": "Financial Services",
    "car_dealer": "Automotive",
    "car_repair": "Automotive",
    "car_wash": "Automotive",
    "gas_station": "Automotive",
    "movie_theater": "Entertainment",
    "amusement_park": "Entertainment",
    "bowling_alley": "Entertainment",
    "museum": "Entertainment",
    "art_gallery": "Entertainment",
    "tourist_attraction": "Entertainment",
    "lodging": "Hotels & Travel",
    "travel_agency": "Hotels & Travel",
    "airport": "Hotels & Travel",
    "real_estate_agency": "Real Estate",
    "lawyer": "Professional Services",
    "plumber": "Home Services",
    "electrician": "Home Services",
    "locksmith": "Home Services",
    "painter": "Home Services",
    "roofing_contractor": "Home Services",
    "pet_store": "Pets",
    "school": "Education",
    "university": "Education",
    "library": "Education",
    "church": "Religious Organizations",
    "mosque": "Religious Organizations",
    "synagogue": "Religious Organizations",
    "park": "Active Life",
    "stadium": "Active Life",
    "supermarket": "Grocery",
    "grocery_or_supermarket": "Grocery",
    "convenience_store": "Grocery",
    "laundry": "Local Services",
    "post_office": "Local Services",
    "parking": "Local Services",
    "local_government_office": "Public Services",
    "fire_station": "Public Services",
    "police": "Public Services",
}


def _map_category(types: list[str]) -> str:
    """Return the first matching Vantage category or 'Other'."""
    for t in types:
        if t in _TYPE_MAP:
            return _TYPE_MAP[t]
    return "Other"


# ── Geo-cell helpers ────────────────────────────────────────────────

def _radius_bucket(radius_m: int) -> int:
    """Round a radius (meters) to standard buckets for cache keys."""
    for bucket in (1000, 3000, 5000, 10000, 25000, 50000):
        if radius_m <= bucket:
            return bucket
    return 50000


def geo_cell_key(lat: float, lng: float, radius_m: int) -> dict:
    """
    Return a dict that uniquely identifies a ~1 km grid cell + radius tier.
    Used as a filter when querying / upserting the geo_cache collection.
    """
    cell_lat = round(lat, 2)   # ~1.1 km resolution
    cell_lng = round(lng, 2)
    return {
        "cell_lat": cell_lat,
        "cell_lng": cell_lng,
        "radius_bucket": _radius_bucket(radius_m),
    }


# ── Main search function ───────────────────────────────────────────

GOOGLE_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"


async def search_google_places(
    lat: float,
    lng: float,
    radius_m: int = 5000,
    keyword: Optional[str] = None,
) -> List[Dict]:
    """
    Call Google Places Nearby Search and return a list of MongoDB-ready dicts.
    Each dict contains: name, place_id, location (GeoJSON), category, etc.
    """
    if not GOOGLE_API_KEY:
        print("⚠️  GOOGLE_API_KEY not set – skipping Places lookup")
        return []

    params = {
        "location": f"{lat},{lng}",
        "radius": radius_m,
        "key": GOOGLE_API_KEY,
    }
    if keyword:
        params["keyword"] = keyword

    all_results: list[dict] = []

    async with httpx.AsyncClient(timeout=15) as client:
        # First page
        resp = await client.get(GOOGLE_NEARBY_URL, params=params)
        data = resp.json()

        # Log API call
        await _log_api_call("nearbysearch", params, data.get("status"), len(data.get("results", [])))

        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            print(f"⚠️  Google Places error: {data.get('status')} – {data.get('error_message', '')}")
            return []

        all_results.extend(data.get("results", []))

        # Follow up to 2 next_page_token pages (max 60 results total)
        for _ in range(2):
            token = data.get("next_page_token")
            if not token:
                break
            # Google requires a short delay before using the token
            import asyncio
            await asyncio.sleep(2)
            resp = await client.get(GOOGLE_NEARBY_URL, params={"pagetoken": token, "key": GOOGLE_API_KEY})
            data = resp.json()
            await _log_api_call("nearbysearch:page", {"pagetoken": token[:20]}, data.get("status"), len(data.get("results", [])))
            all_results.extend(data.get("results", []))

    # Convert to MongoDB-ready documents
    documents = []
    for place in all_results:
        loc = place.get("geometry", {}).get("location", {})
        p_lat = loc.get("lat")
        p_lng = loc.get("lng")
        if p_lat is None or p_lng is None:
            continue

        photo_ref = ""
        photos = place.get("photos", [])
        if photos:
            photo_ref = photos[0].get("photo_reference", "")

        image_url = ""
        if photo_ref:
            image_url = (
                f"https://maps.googleapis.com/maps/api/place/photo"
                f"?maxwidth=400&photo_reference={photo_ref}&key={GOOGLE_API_KEY}"
            )

        doc = {
            "name": place.get("name", "Unknown"),
            "place_id": place.get("place_id"),
            "category": _map_category(place.get("types", [])),
            "description": place.get("vicinity", ""),
            "address": place.get("vicinity", ""),
            "location": {
                "type": "Point",
                "coordinates": [p_lng, p_lat],
            },
            "rating_average": place.get("rating", 0),
            "total_reviews": place.get("user_ratings_total", 0),
            "image": image_url,
            "phone": "",
            "website": "",
            "hours": [],
            "is_claimed": False,
            "owner_id": None,
            "credibility_score": 0.0,
            "live_visibility_score": 0.0,
            "source": "google_places",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        documents.append(doc)

    return documents


async def _log_api_call(endpoint: str, params: dict, status: str, result_count: int):
    """Log every Google API call for auditing and cost tracking."""
    try:
        log_coll = get_api_usage_log_collection()
        await log_coll.insert_one({
            "service": "google_places",
            "endpoint": endpoint,
            "params": {k: v for k, v in params.items() if k != "key"},
            "status": status,
            "result_count": result_count,
            "called_at": datetime.utcnow(),
        })
    except Exception as e:
        print(f"⚠️  Failed to log API call: {e}")
