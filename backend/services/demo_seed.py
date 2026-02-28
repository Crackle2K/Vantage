"""
Demo Mode data seeding for Vantage.

Provides a compact, curated local dataset so Explore can tell the full story
when the surrounding area has weak or sparse real data.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote

from models.activity import ActivityType, CheckInStatus
from services.business_metadata import derive_known_for, generate_short_description
from services.visibility_score import calculate_live_visibility_score

_PALETTE = [
    ("#234E52", "#8FD3D1"),
    ("#6B3E26", "#E8B27C"),
    ("#1E3A5F", "#76B0D7"),
    ("#5E3B76", "#C9A5E2"),
    ("#355834", "#9ED39B"),
    ("#7A2E3A", "#F2A7B1"),
]

_DEMO_BUSINESSES: list[dict[str, Any]] = [
    {
        "place_id": "demo-ossington-lantern",
        "name": "Lantern Coffee House",
        "category": "Cafes & Coffee",
        "photo_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=1200&q=80",
        "address": "214 Ossington Ave",
        "city": "Toronto",
        "offset": (0.0072, -0.0105),
        "review_count": 18,
        "weighted_reviews": 21.5,
        "verified_visits": 14,
        "engagement_actions": 20,
        "last_activity_minutes": 12,
        "checkins_today": 8,
        "trending_score": 14.0,
        "local_confidence": 0.94,
        "business_type": "independent",
        "is_claimed": True,
        "has_deals": True,
        "description": "A warm all-day cafe with house-roasted espresso, pastry drops, and neighborhood regulars from open to close.",
        "known_for": ["Cozy", "House-roasted", "Quiet work"],
        "event_title": "Late Latte Set",
        "event_description": "Extended evening hours with a pastry pairing and acoustic set for the neighborhood crowd.",
    },
    {
        "place_id": "demo-queen-atelier",
        "name": "Atelier North",
        "category": "Shopping",
        "photo_url": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1200&q=80",
        "address": "451 Queen St W",
        "city": "Toronto",
        "offset": (0.0041, -0.0048),
        "review_count": 9,
        "weighted_reviews": 11.6,
        "verified_visits": 6,
        "engagement_actions": 9,
        "last_activity_minutes": 38,
        "checkins_today": 4,
        "trending_score": 9.5,
        "local_confidence": 0.88,
        "business_type": "independent",
        "is_claimed": False,
        "has_deals": False,
        "description": "A design-led independent boutique featuring limited-run home goods, prints, and local maker capsules.",
        "known_for": ["Design-led", "Local makers", "Giftable"],
    },
    {
        "place_id": "demo-harbourline-social",
        "name": "Harbourline Social",
        "category": "Bars & Nightlife",
        "photo_url": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=1200&q=80",
        "address": "88 Front St E",
        "city": "Toronto",
        "offset": (-0.0036, 0.0054),
        "review_count": 22,
        "weighted_reviews": 24.8,
        "verified_visits": 11,
        "engagement_actions": 18,
        "last_activity_minutes": 22,
        "checkins_today": 7,
        "trending_score": 13.2,
        "local_confidence": 0.72,
        "business_type": "chain",
        "is_claimed": True,
        "has_deals": True,
        "description": "Cocktails, DJ-led lounge energy, and polished service built for after-work meetups that stretch late.",
        "known_for": ["Trendy", "Cocktails", "Nightlife"],
        "event_title": "Golden Hour DJ Set",
        "event_description": "A live rooftop-adjacent DJ session with rotating feature cocktails before the late-night rush.",
    },
    {
        "place_id": "demo-park-studio",
        "name": "Parkline Studio",
        "category": "Fitness & Wellness",
        "photo_url": "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=1200&q=80",
        "address": "129 King St E",
        "city": "Toronto",
        "offset": (-0.0051, -0.0038),
        "review_count": 16,
        "weighted_reviews": 19.4,
        "verified_visits": 9,
        "engagement_actions": 13,
        "last_activity_minutes": 55,
        "checkins_today": 5,
        "trending_score": 8.8,
        "local_confidence": 0.91,
        "business_type": "independent",
        "is_claimed": False,
        "has_deals": False,
        "description": "An intimate movement studio blending reformer, mobility, and recovery sessions in a calm premium setting.",
        "known_for": ["Premium", "Quiet", "Recovery"],
    },
    {
        "place_id": "demo-clover-market",
        "name": "Clover Market Hall",
        "category": "Grocery",
        "photo_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=1200&q=80",
        "address": "301 Jarvis St",
        "city": "Toronto",
        "offset": (0.0088, 0.0061),
        "review_count": 7,
        "weighted_reviews": 8.5,
        "verified_visits": 5,
        "engagement_actions": 7,
        "last_activity_minutes": 90,
        "checkins_today": 3,
        "trending_score": 7.4,
        "local_confidence": 0.83,
        "business_type": "independent",
        "is_claimed": False,
        "has_deals": True,
        "description": "A compact neighborhood food hall with prepared meals, pantry staples, and highly local produce rotations.",
        "known_for": ["Neighborhood favorite", "Fresh", "Budget-friendly"],
    },
    {
        "place_id": "demo-studio-mercer",
        "name": "Studio Mercer",
        "category": "Beauty & Spas",
        "photo_url": "https://images.unsplash.com/photo-1521590832167-7bcbfaa6381f?auto=format&fit=crop&w=1200&q=80",
        "address": "52 Mercer St",
        "city": "Toronto",
        "offset": (-0.0027, -0.0082),
        "review_count": 13,
        "weighted_reviews": 15.1,
        "verified_visits": 7,
        "engagement_actions": 10,
        "last_activity_minutes": 28,
        "checkins_today": 4,
        "trending_score": 10.4,
        "local_confidence": 0.86,
        "business_type": "independent",
        "is_claimed": True,
        "has_deals": False,
        "description": "A polished self-care studio known for fast appointments, high-touch service, and a quietly premium finish.",
        "known_for": ["Premium", "Appointments", "Self-care"],
        "event_title": "Glow Session Week",
        "event_description": "A limited run of bundled treatments with evening availability for post-work appointments.",
    },
]


def _demo_image_data_uri(title: str, category: str, color_a: str, color_b: str) -> str:
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_category = category.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 900">
      <defs>
        <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="{color_a}" />
          <stop offset="100%" stop-color="{color_b}" />
        </linearGradient>
      </defs>
      <rect width="1200" height="900" fill="url(#g)" />
      <circle cx="980" cy="180" r="210" fill="rgba(255,255,255,0.12)" />
      <circle cx="180" cy="760" r="240" fill="rgba(255,255,255,0.09)" />
      <text x="90" y="650" fill="white" font-family="Georgia, serif" font-size="92" font-weight="700">{safe_title}</text>
      <text x="96" y="732" fill="rgba(255,255,255,0.82)" font-family="Arial, sans-serif" font-size="34" letter-spacing="4">{safe_category.upper()}</text>
    </svg>
    """.strip()
    return f"data:image/svg+xml;charset=UTF-8,{quote(svg)}"


def _business_doc(seed: dict[str, Any], lat: float, lng: float, index: int, now: datetime) -> dict[str, Any]:
    color_a, color_b = _PALETTE[index % len(_PALETTE)]
    business_lat = lat + seed["offset"][0]
    business_lng = lng + seed["offset"][1]
    fallback_image_url = _demo_image_data_uri(seed["name"], seed["category"], color_a, color_b)
    image_url = str(seed.get("photo_url") or fallback_image_url)
    last_activity_at = now - timedelta(minutes=int(seed["last_activity_minutes"]))
    created_at = now - timedelta(days=14 + (index * 3))
    weighted_reviews = float(seed["weighted_reviews"])
    review_count = int(seed["review_count"])
    verified_visits = int(seed["verified_visits"])
    engagement_actions = int(seed["engagement_actions"])
    potential_engagements = max(review_count + verified_visits, 1)
    visibility = calculate_live_visibility_score(
        verified_visit_count=verified_visits,
        review_count=review_count,
        credibility_weighted_review_count=weighted_reviews,
        last_activity_at=last_activity_at,
        engagement_actions=engagement_actions,
        total_potential_engagements=potential_engagements,
    )
    short_description = generate_short_description(
        category=seed["category"],
        address=seed["address"],
        city=seed["city"],
        existing=seed["description"],
    )
    known_for = derive_known_for(
        category=seed["category"],
        existing=seed["known_for"],
    )
    owner_id = None
    claim_status = None
    if seed["is_claimed"]:
        owner_id = f"{index + 1:024x}"
        claim_status = "verified"

    return {
        "place_id": seed["place_id"],
        "source": "demo_mode",
        "demo_seed": True,
        "name": seed["name"],
        "category": seed["category"],
        "description": seed["description"],
        "short_description": short_description,
        "known_for": known_for,
        "address": seed["address"],
        "city": seed["city"],
        "location": {
            "type": "Point",
            "coordinates": [round(business_lng, 6), round(business_lat, 6)],
        },
        "website": f"https://demo.vantage.local/{seed['place_id']}",
        "image": image_url,
        "image_url": image_url,
        "image_urls": [image_url, fallback_image_url] if image_url != fallback_image_url else [fallback_image_url],
        "is_seed": True,
        "is_claimed": bool(seed["is_claimed"]),
        "claim_status": claim_status,
        "owner_id": owner_id,
        "has_deals": bool(seed["has_deals"]),
        "business_type": seed["business_type"],
        "local_confidence": float(seed["local_confidence"]),
        "rating_average": round(min(5.0, 4.2 + (weighted_reviews / max(review_count, 1)) * 0.18), 2),
        "total_reviews": review_count,
        "review_count": review_count,
        "live_visibility_score": visibility,
        "credibility_score": round(min(100.0, 62 + weighted_reviews * 1.5), 2),
        "is_active_today": int(seed["checkins_today"]) > 0,
        "checkins_today": int(seed["checkins_today"]),
        "trending_score": float(seed["trending_score"]),
        "last_activity_at": last_activity_at,
        "last_verified_at": now - timedelta(minutes=max(5, int(seed["last_activity_minutes"]) - 6)),
        "created_at": created_at,
        "updated_at": now,
        "ranking_components": {
            "verified_visits": verified_visits,
            "credibility_weighted_reviews": weighted_reviews,
            "engagement_actions": engagement_actions,
            "raw_review_count": review_count,
        },
    }


async def seed_demo_dataset(database, lat: float, lng: float) -> None:
    """
    Upsert a curated local demo cluster and refresh matching activity docs.
    Safe to call at startup when DEMO_MODE is enabled.
    """
    businesses = database["businesses"]
    checkins = database["checkins"]
    reviews = database["reviews"]
    owner_posts = database["owner_posts"]
    activity_feed = database["activity_feed"]

    now = datetime.utcnow()
    place_ids = [seed["place_id"] for seed in _DEMO_BUSINESSES]

    for index, seed in enumerate(_DEMO_BUSINESSES):
        business_doc = _business_doc(seed, lat, lng, index, now)
        await businesses.update_one(
            {"place_id": seed["place_id"]},
            {"$set": business_doc, "$setOnInsert": {"created_at": business_doc["created_at"]}},
            upsert=True,
        )

    business_docs = await businesses.find(
        {"place_id": {"$in": place_ids}},
        {"_id": 1, "place_id": 1, "name": 1, "category": 1, "image_url": 1, "description": 1},
    ).to_list(length=len(place_ids))
    business_by_place_id = {doc["place_id"]: doc for doc in business_docs if doc.get("place_id")}

    await checkins.delete_many({"demo_seed": True})
    await reviews.delete_many({"demo_seed": True})
    await owner_posts.delete_many({"demo_seed": True})
    await activity_feed.delete_many({"demo_seed": True})

    checkin_docs: list[dict[str, Any]] = []
    review_docs: list[dict[str, Any]] = []
    owner_post_docs: list[dict[str, Any]] = []
    activity_docs: list[dict[str, Any]] = []

    for index, seed in enumerate(_DEMO_BUSINESSES):
        business = business_by_place_id.get(seed["place_id"])
        if not business or not business.get("_id"):
            continue

        business_id = str(business["_id"])
        created_at = now - timedelta(minutes=max(5, int(seed["last_activity_minutes"])))

        checkin_docs.append(
            {
                "demo_seed": True,
                "user_id": f"demo-user-{index + 1}",
                "business_id": business_id,
                "status": CheckInStatus.GEO_VERIFIED.value,
                "latitude": lat + seed["offset"][0],
                "longitude": lng + seed["offset"][1],
                "distance_from_business": 18 + (index * 4),
                "created_at": created_at,
                "confirmed_by": [],
            }
        )

        review_docs.append(
            {
                "demo_seed": True,
                "business_id": business_id,
                "user_id": f"demo-reviewer-{index + 1}",
                "rating": round(min(5.0, 4.0 + (index * 0.15)), 1),
                "comment": f"{seed['name']} feels active, polished, and worth returning to when you want a reliable local option.",
                "created_at": created_at - timedelta(minutes=7),
            }
        )

        activity_docs.append(
            {
                "demo_seed": True,
                "activity_type": ActivityType.REVIEW.value,
                "user_id": f"demo-reviewer-{index + 1}",
                "user_name": "Community member",
                "business_id": business_id,
                "business_name": seed["name"],
                "business_category": seed["category"],
                "title": f"New review at {seed['name']}",
                "description": "Fresh platform feedback added in demo mode.",
                "likes": 0,
                "comments": 0,
                "created_at": created_at - timedelta(minutes=7),
            }
        )

        if seed.get("has_deals"):
            activity_docs.append(
                {
                    "demo_seed": True,
                    "activity_type": ActivityType.DEAL_POSTED.value,
                    "business_id": business_id,
                    "business_name": seed["name"],
                    "business_category": seed["category"],
                    "title": f"{seed['name']} posted a promo",
                    "description": "Limited-time offer highlighted for local discovery demos.",
                    "likes": 0,
                    "comments": 0,
                    "created_at": created_at - timedelta(minutes=3),
                }
            )

        if seed.get("event_title"):
            owner_post_docs.append(
                {
                    "demo_seed": True,
                    "business_id": business_id,
                    "title": seed["event_title"],
                    "description": seed["event_description"],
                    "start_time": now + timedelta(days=1, hours=index),
                    "end_time": now + timedelta(days=1, hours=index + 3),
                    "created_at": created_at - timedelta(minutes=2),
                    "image_url": business.get("image_url"),
                }
            )
            activity_docs.append(
                {
                    "demo_seed": True,
                    "activity_type": ActivityType.EVENT_CREATED.value,
                    "business_id": business_id,
                    "business_name": seed["name"],
                    "business_category": seed["category"],
                    "title": seed["event_title"],
                    "description": seed["event_description"],
                    "likes": 0,
                    "comments": 0,
                    "created_at": created_at - timedelta(minutes=2),
                }
            )

    if checkin_docs:
        await checkins.insert_many(checkin_docs, ordered=False)
    if review_docs:
        await reviews.insert_many(review_docs, ordered=False)
    if owner_post_docs:
        await owner_posts.insert_many(owner_post_docs, ordered=False)
    if activity_docs:
        await activity_feed.insert_many(activity_docs, ordered=False)
