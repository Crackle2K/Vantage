from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DealBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=500)
    discount_percent: float = Field(..., ge=0, le=100, description="Discount percentage (0-100)")
    expires_at: datetime

class DealCreate(BaseModel):
    business_id: str
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=500)
    discount_percent: float = Field(..., ge=0, le=100, description="Discount percentage (0-100)")
    expires_at: datetime
    active: bool = True

class DealUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    discount_percent: Optional[float] = Field(None, ge=0, le=100)
    expires_at: Optional[datetime] = None
    active: Optional[bool] = None

class Deal(DealBase):
    id: str
    business_id: str
    active: bool = True
    created_at: datetime
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "business_id": "507f1f77bcf86cd799439012",
                "title": "Happy Hour Special",
                "description": "Get 20% off all drinks from 4-6 PM every weekday",
                "discount_percent": 20.0,
                "expires_at": "2026-03-31T23:59:59Z",
                "active": True,
                "created_at": "2026-02-01T10:00:00Z"
            }
        }

class DealWithBusiness(Deal):
    business_name: str
    business_category: str
