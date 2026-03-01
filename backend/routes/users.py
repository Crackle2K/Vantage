from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from models.user import User, UserUpdate, UserPreferencesUpdate
from models.auth import get_current_user
from database.mongodb import get_users_collection

router = APIRouter()

def _serialize_user(user: dict) -> User:
    user["id"] = str(user["_id"])
    if "created_at" in user and user["created_at"]:
        user["created_at"] = user["created_at"].isoformat()
    return User(**user)

def _normalize_text_list(values: list[str], limit: int) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value or "").strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(cleaned[:32])
        if len(normalized) >= limit:
            break
    return normalized

@router.get("/{user_id}", response_model=User)
async def get_user_profile(user_id: str):
    try:
        users_collection = get_users_collection()
    except Exception as db_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {str(db_error)}"
        )
    from bson import ObjectId
    from bson.errors import InvalidId
    try:
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return _serialize_user(user)

@router.put("/me", response_model=User)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    try:
        users_collection = get_users_collection()
    except Exception as db_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {str(db_error)}"
        )
    update_data = {}
    if user_update.name is not None:
        update_data["name"] = user_update.name
    if user_update.profile_picture is not None:
        update_data["profile_picture"] = user_update.profile_picture
    if user_update.about_me is not None:
        update_data["about_me"] = user_update.about_me
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    update_data["updated_at"] = datetime.utcnow()
    from bson import ObjectId
    result = await users_collection.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": update_data}
    )
    if result.modified_count == 0:
        user = await users_collection.find_one({"_id": ObjectId(current_user.id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    updated_user = await users_collection.find_one({"_id": ObjectId(current_user.id)})
    return _serialize_user(updated_user)

@router.put("/preferences", response_model=User)
async def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user)
):
    try:
        users_collection = get_users_collection()
    except Exception as db_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {str(db_error)}"
        )

    from bson import ObjectId

    update_data = {
        "preferred_categories": _normalize_text_list(preferences_update.preferred_categories, 8),
        "preferred_vibes": _normalize_text_list(preferences_update.preferred_vibes, 10),
        "prefer_independent": round(float(preferences_update.prefer_independent), 3),
        "price_pref": preferences_update.price_pref.value if preferences_update.price_pref else None,
        "discovery_mode": preferences_update.discovery_mode.value,
        "preferences_completed": bool(preferences_update.preferences_completed),
        "updated_at": datetime.utcnow(),
    }

    await users_collection.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": update_data}
    )

    updated_user = await users_collection.find_one({"_id": ObjectId(current_user.id)})
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return _serialize_user(updated_user)
