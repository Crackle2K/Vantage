"""
Discovery Routes for Vantage
Smart business search + verified visits + live visibility scoring

Key endpoint: GET /discover
  1. Query MongoDB (2dsphere) for businesses near lat/lng
  2. If >= 20 results → return sorted by live_visibility_score
  3. If < 20 AND the area hasn't been fetched recently (geo_cache TTL)
     → call Google Places → bulk-insert new businesses → re-query
  4. Always return results sorted by live_visibility_score descending

COST-SAVING RULES:
  • geo_cache stores which lat/lng cells have been fetched and when.
  • If a cell was fetched within the last 24 hours we NEVER call Google again.
  • All businesses from Google are persisted with a unique place_id index
    so they're available forever without re-fetching.
  • Every Google API call is logged in api_usage_log.

POST /visits — verified visit submission (Haversine ≤ 100 m)
"""

import math
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Query
from bson import ObjectId

from models.user import User
from models.auth import get_current_user
from database.mongodb import (
    get_businesses_collection,
    get_visits_collection,
    get_reviews_collection,
    get_checkins_collection,
    get_geo_cache_collection,
)
from services.google_places import search_google_places, geo_cell_key
from services.visibility_score import calculate_live_visibility_score

router = APIRouter()

MIN_RESULTS = 20         # Threshold before considering a Google backfill
CACHE_TTL_HOURS = 24     # Don't re-fetch the same area within this window


def business_helper(doc: dict) -> dict:
    """Convert a MongoDB business document for the API response."""
    if doc is None:
        return doc
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    doc.setdefault("rating", doc.pop("rating_average", 0.0))
    doc.setdefault("review_count", doc.pop("total_reviews", 0))
    doc.setdefault("has_deals", False)
    if "owner_id" in doc and doc["owner_id"]:
        doc["owner_id"] = str(doc["owner_id"])
    return doc


# ── Smart Search ────────────────────────────────────────────────────

@router.get("/discover")
async def discover_businesses(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: float = Query(5, ge=0.1, le=50, description="Radius in km"),
    category: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
):
    """
    Smart business discovery with aggressive caching.

      1. Search MongoDB via 2dsphere index.
      2. If >= 20 results, return immediately (no API call).
      3. If < 20 results, check geo_cache:
         a. If this area was fetched within the last 24 hours → skip Google,
            return whatever we have from MongoDB.
         b. If NOT cached → call Google Places, bulk-insert new businesses,
            mark the cell as cached, then re-query MongoDB.
      4. Always sorted by live_visibility_score descending.
    """
    businesses = get_businesses_collection()
    geo_cache = get_geo_cache_collection()
    radius_meters = radius * 1000

    # ── Step 1: MongoDB geo query ───────────────────────────────────
    geo_filter = {
        "location": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                "$maxDistance": radius_meters,
            }
        }
    }
    if category:
        geo_filter["category"] = category

    cursor = businesses.find(geo_filter).limit(limit)
    results = await cursor.to_list(length=limit)

    # ── Step 2: Enough results? Return immediately ──────────────────
    if len(results) >= MIN_RESULTS:
        results.sort(key=lambda b: b.get("live_visibility_score", 0), reverse=True)
        return [business_helper(b) for b in results]

    # ── Step 3: Check geo cache before calling Google ───────────────
    cell = geo_cell_key(lat, lng, int(radius_meters))
    cache_cutoff = datetime.utcnow() - timedelta(hours=CACHE_TTL_HOURS)

    cached = await geo_cache.find_one({
        **cell,
        "fetched_at": {"$gte": cache_cutoff},
    })

    if cached:
        # Already fetched this area recently — return what MongoDB has
        results.sort(key=lambda b: b.get("live_visibility_score", 0), reverse=True)
        return [business_helper(b) for b in results]

    # ── Step 4: Call Google Places (cache miss) ─────────────────────
    new_places = await search_google_places(lat, lng, int(radius_meters))

    if new_places:
        # Bulk dedup: collect all incoming place_ids, query MongoDB once
        incoming_place_ids = [p["place_id"] for p in new_places]
        existing_cursor = businesses.find(
            {"place_id": {"$in": incoming_place_ids}},
            {"place_id": 1},
        )
        existing_ids = {doc["place_id"] async for doc in existing_cursor}

        to_insert = [p for p in new_places if p["place_id"] not in existing_ids]
        if to_insert:
            await businesses.insert_many(to_insert, ordered=False)
            print(f"📍 Backfilled {len(to_insert)} businesses from Google Places")

    # Mark this cell as cached so we don't call Google again for 24 h
    await geo_cache.update_one(
        cell,
        {"$set": {**cell, "fetched_at": datetime.utcnow(), "result_count": len(new_places)}},
        upsert=True,
    )

    # ── Step 5: Re-query and return ─────────────────────────────────
    cursor = businesses.find(geo_filter).limit(limit)
    results = await cursor.to_list(length=limit)
    results.sort(key=lambda b: b.get("live_visibility_score", 0), reverse=True)

    return [business_helper(b) for b in results]


# ── Verified Visits ─────────────────────────────────────────────────

VISIT_MAX_DISTANCE_METERS = 100  # Must be within 100 m


def _haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in meters between two lat/lng pairs."""
    R = 6_371_000  # Earth radius in meters
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.post("/visits", status_code=status.HTTP_201_CREATED)
async def submit_visit(
    business_id: str = Query(...),
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a verified visit.
    - User location must be within 100 m of the business.
    - On success the business's live_visibility_score is recalculated.
    """
    businesses = get_businesses_collection()
    visits = get_visits_collection()

    if not ObjectId.is_valid(business_id):
        raise HTTPException(status_code=400, detail="Invalid business ID")

    business = await businesses.find_one({"_id": ObjectId(business_id)})
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Check distance
    biz_loc = business.get("location", {})
    coords = biz_loc.get("coordinates")
    if not coords or len(coords) < 2:
        raise HTTPException(status_code=400, detail="Business has no location data")

    biz_lng, biz_lat = coords
    distance = _haversine_meters(lat, lng, biz_lat, biz_lng)

    if distance > VISIT_MAX_DISTANCE_METERS:
        raise HTTPException(
            status_code=400,
            detail=f"You are {round(distance)}m away. Must be within {VISIT_MAX_DISTANCE_METERS}m.",
        )

    # Rate-limit: 1 verified visit per business per user per 4 hours
    cutoff = datetime.utcnow() - timedelta(hours=4)
    recent = await visits.find_one({
        "user_id": current_user.id,
        "business_id": business_id,
        "created_at": {"$gte": cutoff},
    })
    if recent:
        raise HTTPException(status_code=400, detail="Already visited recently. Try again later.")

    visit_doc = {
        "user_id": current_user.id,
        "business_id": business_id,
        "latitude": lat,
        "longitude": lng,
        "distance_meters": round(distance, 1),
        "verified": True,
        "created_at": datetime.utcnow(),
    }
    await visits.insert_one(visit_doc)

    # Recalculate live visibility score
    await _recalculate_visibility(business_id)

    return {"status": "verified", "distance_meters": round(distance, 1)}


# ── Score Recalculation ─────────────────────────────────────────────

async def _recalculate_visibility(business_id: str):
    """Recompute and persist the live_visibility_score for a business."""
    businesses = get_businesses_collection()
    visits = get_visits_collection()
    reviews = get_reviews_collection()
    checkins = get_checkins_collection()

    verified_visit_count = await visits.count_documents({"business_id": business_id, "verified": True})
    review_count = await reviews.count_documents({"business_id": business_id})

    # Last activity timestamp (most recent of visit or review)
    last_visit = await visits.find_one({"business_id": business_id}, sort=[("created_at", -1)])
    last_review = await reviews.find_one({"business_id": business_id}, sort=[("created_at", -1)])

    timestamps = []
    if last_visit:
        timestamps.append(last_visit["created_at"])
    if last_review:
        timestamps.append(last_review["created_at"])
    last_activity_at = max(timestamps) if timestamps else None

    # Engagement: confirmations on checkins for this business
    pipeline = [
        {"$match": {"business_id": business_id}},
        {"$group": {"_id": None, "total": {"$sum": "$confirmations"}}},
    ]
    agg = await checkins.aggregate(pipeline).to_list(1)
    engagement_actions = agg[0]["total"] if agg else 0
    total_potential = max(verified_visit_count + review_count, 1)

    score = calculate_live_visibility_score(
        verified_visit_count=verified_visit_count,
        review_count=review_count,
        last_activity_at=last_activity_at,
        engagement_actions=engagement_actions,
        total_potential_engagements=total_potential,
    )

    await businesses.update_one(
        {"_id": ObjectId(business_id)},
        {"$set": {"live_visibility_score": score}},
    )
