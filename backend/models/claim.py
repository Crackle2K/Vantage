from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class ClaimStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    REVOKED = "revoked"

class VerificationMethod(str, Enum):
    EMAIL_DOMAIN = "email_domain"
    PHONE_CALL = "phone_call"
    DOCUMENT = "document"
    IN_PERSON = "in_person"
    COMMUNITY = "community"

class BusinessClaim(BaseModel):
    id: str
    business_id: str
    user_id: str
    status: ClaimStatus = ClaimStatus.PENDING
    verification_method: Optional[VerificationMethod] = None
    verification_notes: Optional[str] = None
    owner_name: str = Field(..., min_length=2, max_length=100)
    owner_role: str = Field(default="owner", max_length=50)
    owner_phone: Optional[str] = None
    owner_email: Optional[str] = None
    proof_description: Optional[str] = Field(None, max_length=500)
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

    class Config:
        from_attributes = True

class ClaimCreate(BaseModel):
    business_id: str
    owner_name: str = Field(..., min_length=2, max_length=100)
    owner_role: str = Field(default="owner", max_length=50)
    owner_phone: Optional[str] = None
    owner_email: Optional[str] = None
    proof_description: Optional[str] = Field(None, max_length=500)

class ClaimReview(BaseModel):
    status: ClaimStatus
    verification_method: Optional[VerificationMethod] = None
    verification_notes: Optional[str] = Field(None, max_length=500)
