"""
<<<<<<< Updated upstream
Live Visibility Score
Calculates a 0–100 score based on verified visits, reviews, recency, and engagement.

Formula weights:
  0.35 * verified_visits (normalised to /50)
  0.30 * reviews         (normalised to /30)
  0.20 * recency_factor  (1.0 if < 7 days, decays to 0 over 90 days)
  0.15 * engagement_rate (actions / potential, capped at 1.0)
=======
Live Visibility Score for Vantage
Determines how prominently a business appears in search results.

Formula:
  0.35 * verified_visit_count
  0.30 * review_count
  0.20 * recency_factor      (how recent the last activity was)
  0.15 * engagement_rate      (likes, confirmations, etc.)

All components are normalised to 0–100 before weighting so the
final score is also on a 0–100 scale.
>>>>>>> Stashed changes
"""

from datetime import datetime, timedelta
from typing import Optional


<<<<<<< Updated upstream
=======
def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


>>>>>>> Stashed changes
def calculate_live_visibility_score(
    verified_visit_count: int = 0,
    review_count: int = 0,
    last_activity_at: Optional[datetime] = None,
<<<<<<< Updated upstream
    engagement_actions: int = 0,
    total_potential_engagements: int = 1,
) -> float:
    """Return a visibility score between 0 and 100."""

    # Normalise visits (cap at 50 for a perfect sub-score)
    visit_score = min(verified_visit_count / 50, 1.0)

    # Normalise reviews (cap at 30)
    review_score = min(review_count / 30, 1.0)

    # Recency: 1.0 if activity in last 7 days, linear decay to 0 at 90 days
    if last_activity_at is None:
        recency = 0.0
    else:
        days_ago = (datetime.utcnow() - last_activity_at).total_seconds() / 86400
        if days_ago <= 7:
            recency = 1.0
        elif days_ago >= 90:
            recency = 0.0
        else:
            recency = 1.0 - (days_ago - 7) / (90 - 7)

    # Engagement rate
    engagement = min(engagement_actions / max(total_potential_engagements, 1), 1.0)

    raw = (
        0.35 * visit_score
        + 0.30 * review_score
        + 0.20 * recency
        + 0.15 * engagement
    )

    return round(raw * 100, 2)
=======
    engagement_actions: int = 0,       # likes + confirmations + comments
    total_potential_engagements: int = 1,  # visits + reviews (denominator)
) -> float:
    """
    Return a score in [0, 100].

    Each component is normalised to 0-100 before applying its weight.
    """

    # ── 1. Verified visits  (35 %) ──────────────────────────────────
    # Log-scale: 50 verified visits → 100
    visit_norm = _clamp((verified_visit_count / 50) * 100)

    # ── 2. Review count  (30 %) ─────────────────────────────────────
    # Log-scale: 30 reviews → 100
    review_norm = _clamp((review_count / 30) * 100)

    # ── 3. Recency factor  (20 %) ──────────────────────────────────
    if last_activity_at:
        hours_ago = (datetime.utcnow() - last_activity_at).total_seconds() / 3600
        if hours_ago <= 1:
            recency = 100
        elif hours_ago <= 24:
            recency = 80
        elif hours_ago <= 72:
            recency = 50
        elif hours_ago <= 168:       # 1 week
            recency = 25
        else:
            recency = 5
    else:
        recency = 0.0

    # ── 4. Engagement rate  (15 %) ──────────────────────────────────
    denom = max(total_potential_engagements, 1)
    raw_rate = engagement_actions / denom
    engagement_norm = _clamp(raw_rate * 100)

    score = (
        0.35 * visit_norm
        + 0.30 * review_norm
        + 0.20 * recency
        + 0.15 * engagement_norm
    )

    return round(_clamp(score), 2)
>>>>>>> Stashed changes
