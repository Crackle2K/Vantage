"""
<<<<<<< Updated upstream
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
=======
Google Places Service for Vantage
Backend-only usage — the API key is NEVER sent to the frontend.

Calls Google Places Nearby Search to backfill businesses when
our MongoDB database has fewer than 20 results for a location.

COST-SAVING STRATEGY:
  1. Every API call is logged in the `api_usage_log` collection.
  2. A `geo_cache` collection tracks which geographic cells have
     already been fetched and when (24-hour TTL).
  3. The caller (discovery.py) checks the geo cache BEFORE calling
     this service so duplicate fetches never happen.
  4. All results are immediately persisted into `businesses` with a
     unique `place_id` index so we never insert duplicates.
"""

import math
import httpx
from typing import List, Optional
from datetime import datetime
>>>>>>> Stashed changes

from config import GOOGLE_API_KEY
from database.mongodb import get_api_usage_log_collection

<<<<<<< Updated upstream
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
=======
PLACES_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

# Map Google Places types → Vantage categories
_GOOGLE_TYPE_MAP = {
    "restaurant": "food",
    "cafe": "food",
    "bakery": "food",
    "bar": "food",
    "meal_delivery": "food",
    "meal_takeaway": "food",
    "food": "food",
    "store": "retail",
    "shopping_mall": "retail",
    "clothing_store": "retail",
    "electronics_store": "retail",
    "convenience_store": "retail",
    "supermarket": "retail",
    "shoe_store": "retail",
    "book_store": "retail",
    "jewelry_store": "retail",
    "home_goods_store": "retail",
    "hardware_store": "retail",
    "department_store": "retail",
    "gym": "health",
    "health": "health",
    "hospital": "health",
    "pharmacy": "health",
    "dentist": "health",
    "doctor": "health",
    "physiotherapist": "health",
    "spa": "beauty",
    "hair_care": "beauty",
    "beauty_salon": "beauty",
    "movie_theater": "entertainment",
    "amusement_park": "entertainment",
    "bowling_alley": "entertainment",
    "night_club": "entertainment",
    "stadium": "entertainment",
    "museum": "entertainment",
    "art_gallery": "entertainment",
    "zoo": "entertainment",
    "school": "education",
    "university": "education",
    "library": "education",
    "car_repair": "automotive",
    "car_dealer": "automotive",
    "car_wash": "automotive",
    "gas_station": "automotive",
    "plumber": "home",
    "electrician": "home",
    "painter": "home",
    "moving_company": "home",
    "locksmith": "home",
    "roofing_contractor": "home",
    "laundry": "services",
    "lawyer": "services",
    "accounting": "services",
    "insurance_agency": "services",
    "real_estate_agency": "services",
    "travel_agency": "services",
    "bank": "services",
    "post_office": "services",
}


def _map_category(google_types: List[str]) -> str:
    """Pick the best Vantage category from a list of Google types."""
    for t in google_types:
        if t in _GOOGLE_TYPE_MAP:
            return _GOOGLE_TYPE_MAP[t]
    return "other"


def _photo_url(photo_ref: Optional[str], max_width: int = 400) -> Optional[str]:
    """Build a Google Places photo URL (proxied through our backend later if needed)."""
    if not photo_ref or not GOOGLE_API_KEY:
        return None
    return (
        f"https://maps.googleapis.com/maps/api/place/photo"
        f"?maxwidth={max_width}&photo_reference={photo_ref}&key={GOOGLE_API_KEY}"
    )
>>>>>>> Stashed changes


async def search_google_places(
    lat: float,
    lng: float,
<<<<<<< Updated upstream
    radius_m: int = 5000,
    keyword: Optional[str] = None,
) -> List[Dict]:
    """
    Call Google Places Nearby Search and return a list of MongoDB-ready dicts.
    Each dict contains: name, place_id, location (GeoJSON), category, etc.
    """
    if not GOOGLE_API_KEY:
        print("⚠️  GOOGLE_API_KEY not set – skipping Places lookup")
=======
    radius_meters: int = 5000,
    keyword: Optional[str] = None,
) -> List[dict]:
    """
    Call Google Places Nearby Search and return a list of dicts
    ready for MongoDB insertion.

    Every call is logged to `api_usage_log` so we can track spend.
    Returns an empty list (never crashes) if the API key is missing
    or the API call fails.
    """
    if not GOOGLE_API_KEY:
        print("⚠️  GOOGLE_API_KEY not set — skipping Google Places backfill")
>>>>>>> Stashed changes
        return []

    params = {
        "location": f"{lat},{lng}",
<<<<<<< Updated upstream
        "radius": radius_m,
=======
        "radius": str(radius_meters),
>>>>>>> Stashed changes
        "key": GOOGLE_API_KEY,
    }
    if keyword:
        params["keyword"] = keyword

<<<<<<< Updated upstream
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
=======
    api_log = get_api_usage_log_collection()
    log_entry = {
        "service": "google_places_nearby",
        "lat": lat,
        "lng": lng,
        "radius_meters": radius_meters,
        "keyword": keyword,
        "timestamp": datetime.utcnow(),
        "status": None,
        "results_count": 0,
        "error": None,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(PLACES_NEARBY_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        print(f"⚠️  Google Places API error: {exc}")
        log_entry["status"] = "error"
        log_entry["error"] = str(exc)
        try:
            await api_log.insert_one(log_entry)
        except Exception:
            pass
        return []

    api_status = data.get("status", "UNKNOWN")
    log_entry["status"] = api_status

    if api_status not in ("OK", "ZERO_RESULTS"):
        print(f"⚠️  Google Places API status: {api_status} — {data.get('error_message', '')}")
        log_entry["error"] = data.get("error_message", "")
        try:
            await api_log.insert_one(log_entry)
        except Exception:
            pass
        return []

    results: List[dict] = []
    for place in data.get("results", []):
        loc = place.get("geometry", {}).get("location", {})
        lat_p = loc.get("lat")
        lng_p = loc.get("lng")
        if lat_p is None or lng_p is None:
            continue

        photo_ref = None
        photos = place.get("photos")
        if photos and len(photos) > 0:
            photo_ref = photos[0].get("photo_reference")

        results.append({
            "place_id": place["place_id"],
            "name": place.get("name", "Unknown"),
            "category": _map_category(place.get("types", [])),
            "description": place.get("vicinity", ""),
            "address": place.get("vicinity", ""),
            "city": "",  # Not reliably available from Nearby Search
            "location": {
                "type": "Point",
                "coordinates": [lng_p, lat_p],  # GeoJSON: [lng, lat]
            },
            "rating_average": place.get("rating", 0.0),
            "total_reviews": place.get("user_ratings_total", 0),
            "phone": None,
            "email": None,
            "website": None,
            "image_url": _photo_url(photo_ref),
            "is_seed": False,
>>>>>>> Stashed changes
            "is_claimed": False,
            "owner_id": None,
            "credibility_score": 0.0,
            "live_visibility_score": 0.0,
<<<<<<< Updated upstream
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
=======
            "is_active_today": False,
            "checkins_today": 0,
            "trending_score": 0.0,
            "has_deals": False,
            "created_at": datetime.utcnow(),
        })

    # Log the successful call with result count
    log_entry["results_count"] = len(results)
    try:
        await api_log.insert_one(log_entry)
    except Exception:
        pass

    return results


# ── Geo-cell helpers ────────────────────────────────────────────────
# We round coordinates to ~1 km grid cells so that nearby searches
# hitting roughly the same area share a single cache entry.

CELL_PRECISION = 2  # 2 decimal places ≈ 1.1 km at equator


def geo_cell_key(lat: float, lng: float, radius_meters: int) -> dict:
    """
    Return a dict that uniquely identifies the geographic cell
    for cache lookup / upsert.
    """
    # Bucket radius into 1km, 3km, 5km, 10km, 25km, 50km
    if radius_meters <= 1500:
        bucket = 1000
    elif radius_meters <= 4000:
        bucket = 3000
    elif radius_meters <= 7500:
        bucket = 5000
    elif radius_meters <= 15000:
        bucket = 10000
    elif radius_meters <= 35000:
        bucket = 25000
    else:
        bucket = 50000

    return {
        "cell_lat": round(lat, CELL_PRECISION),
        "cell_lng": round(lng, CELL_PRECISION),
        "radius_bucket": bucket,
    }
>>>>>>> Stashed changes
