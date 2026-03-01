from datetime import datetime, timedelta
from typing import Optional

def calculate_match_score(
    business: dict,
    user_category_preference: Optional[str] = None,
    max_reviews: int = 500
) -> float:
    rating_score = float(business.get("rating_average", 0.0))
    rating_component = rating_score * 0.4
    total_reviews = business.get("total_reviews", 0)
    popularity_normalized = min(total_reviews / max_reviews, 1.0) * 5.0
    popularity_component = popularity_normalized * 0.3
    business_category = business.get("category", "")
    if user_category_preference and business_category == user_category_preference:
        category_match_score = 5.0
    else:
        category_match_score = 2.5
    category_component = category_match_score * 0.2
    created_at = business.get("created_at")
    if created_at:
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                created_at = datetime.utcnow()
        days_old = (datetime.utcnow() - created_at).days
        if days_old <= 30:
            recent_activity_score = 5.0
        elif days_old <= 90:
            recent_activity_score = 4.0
        elif days_old <= 180:
            recent_activity_score = 3.0
        elif days_old <= 365:
            recent_activity_score = 2.0
        else:
            recent_activity_score = 1.0
    else:
        recent_activity_score = 2.5
    recent_activity_component = recent_activity_score * 0.1
    total_score = (
        rating_component +
        popularity_component +
        category_component +
        recent_activity_component
    )
    return round(total_score, 2)

def calculate_popularity_score(total_reviews: int, max_reviews: int = 500) -> float:
    return round(min(total_reviews / max_reviews, 1.0) * 5.0, 2)

def calculate_recency_score(created_at: datetime) -> float:
    days_old = (datetime.utcnow() - created_at).days
    if days_old <= 30:
        return 5.0
    elif days_old <= 90:
        return 4.0
    elif days_old <= 180:
        return 3.0
    elif days_old <= 365:
        return 2.0
    else:
        return 1.0

def rank_businesses(businesses: list, user_category_preference: Optional[str] = None) -> list:
    for business in businesses:
        business["match_score"] = calculate_match_score(business, user_category_preference)
    ranked = sorted(businesses, key=lambda x: x.get("match_score", 0), reverse=True)
    return ranked
