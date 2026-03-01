from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class CategoryEnum(str, Enum):
    FOOD = "food"
    RETAIL = "retail"
    SERVICES = "services"
    ENTERTAINMENT_LOWER = "entertainment"
    HEALTH = "health"
    EDUCATION_LOWER = "education"
    AUTOMOTIVE_LOWER = "automotive"
    HOME = "home"
    BEAUTY_LOWER = "beauty"
    OTHER_LOWER = "other"
    RESTAURANTS = "Restaurants"
    CAFES = "Cafes & Coffee"
    BARS = "Bars & Nightlife"
    SHOPPING = "Shopping"
    FITNESS = "Fitness & Wellness"
    BEAUTY = "Beauty & Spas"
    HEALTH_MEDICAL = "Health & Medical"
    FINANCIAL = "Financial Services"
    AUTOMOTIVE = "Automotive"
    ENTERTAINMENT = "Entertainment"
    HOTELS = "Hotels & Travel"
    PROFESSIONAL = "Professional Services"
    HOME_SERVICES = "Home Services"
    PETS = "Pets"
    EDUCATION = "Education"
    GROCERY = "Grocery"
    LOCAL_SERVICES = "Local Services"
    ACTIVE_LIFE = "Active Life"
    PUBLIC_SERVICES = "Public Services"
    RELIGIOUS = "Religious Organizations"
    OTHER = "Other"

class GeoLocation(BaseModel):
    type: str = "Point"
    coordinates: List[float] = Field(..., min_length=2, max_length=2)
    class Config:
        json_schema_extra = {
            "example": {
                "type": "Point",
                "coordinates": [-79.3832, 43.6532]
            }
        }

class BusinessBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    category: CategoryEnum
    description: str = Field(..., max_length=1000)
    address: str = Field(..., max_length=300)
    city: str = Field(..., max_length=100)

class BusinessCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    category: CategoryEnum
    description: str = Field(..., max_length=1000)
    address: str = Field(..., max_length=300)
    city: str = Field(..., max_length=100)
    location: GeoLocation
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    image_url: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list, min_length=0, max_length=8)
    short_description: Optional[str] = Field(None, max_length=160)
    known_for: List[str] = Field(default_factory=list, min_length=0, max_length=6)

class BusinessUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    category: Optional[CategoryEnum] = None
    description: Optional[str] = Field(None, max_length=1000)
    address: Optional[str] = Field(None, max_length=300)
    city: Optional[str] = Field(None, max_length=100)
    location: Optional[GeoLocation] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    image_url: Optional[str] = None
    image_urls: Optional[List[str]] = Field(None, min_length=0, max_length=8)
    short_description: Optional[str] = Field(None, max_length=160)
    known_for: Optional[List[str]] = Field(None, min_length=0, max_length=6)

class BusinessProfileUpdate(BaseModel):
    short_description: Optional[str] = Field(None, max_length=160)
    known_for: Optional[List[str]] = Field(None, min_length=0, max_length=6)

class Business(BusinessBase):
    id: str
    owner_id: Optional[str] = None
    place_id: Optional[str] = None
    location: Optional[GeoLocation] = None
    rating: float = Field(default=0.0, ge=0, le=5)
    review_count: int = Field(default=0, ge=0)
    has_deals: bool = False
    created_at: Optional[datetime] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    image_url: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list)
    short_description: Optional[str] = Field(default=None, max_length=160)
    known_for: List[str] = Field(default_factory=list, min_length=0, max_length=6)

    is_claimed: bool = False
    claim_status: Optional[str] = None
    is_seed: bool = True

    credibility_score: float = 0.0
    live_visibility_score: float = 0.0
    local_confidence: float = 0.0

    is_active_today: bool = False
    checkins_today: int = 0
    trending_score: float = 0.0
    last_activity_at: Optional[datetime] = None
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "owner_id": "507f1f77bcf86cd799439012",
                "name": "Joe's Coffee Shop",
                "category": "food",
                "description": "Best coffee in town",
                "address": "123 Main Street",
                "city": "Toronto",
                "location": {
                    "type": "Point",
                    "coordinates": [-79.3832, 43.6532]
                },
                "rating_average": 4.5,
                "total_reviews": 42,
                "created_at": "2026-01-15T10:30:00Z"
            }
        }
