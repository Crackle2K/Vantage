from datetime import datetime
from pydantic import BaseModel

class SavedRecord(BaseModel):
    user_id: str
    business_id: str
    created_at: datetime

class SavedMutationResult(BaseModel):
    business_id: str
    saved: bool
