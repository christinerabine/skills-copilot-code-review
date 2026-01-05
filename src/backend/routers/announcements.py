"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


@router.get("")
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all active announcements (between start_date and expiration_date)"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Query for announcements that are currently active
    query = {
        "expiration_date": {"$gte": current_date}
    }
    
    announcements = list(announcements_collection.find(query))
    
    # Filter by start_date if present, and convert ObjectId to string
    active_announcements = []
    for announcement in announcements:
        # Check if start_date exists and if we're past it
        if announcement.get("start_date"):
            if announcement["start_date"] <= current_date:
                announcement["_id"] = str(announcement["_id"])
                active_announcements.append(announcement)
        else:
            # No start_date means it's always active (until expiration)
            announcement["_id"] = str(announcement["_id"])
            active_announcements.append(announcement)
    
    return active_announcements


@router.get("/all")
def get_all_announcements(username: str) -> List[Dict[str, Any]]:
    """Get all announcements (for management purposes - requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    announcements = list(announcements_collection.find())
    
    # Convert ObjectId to string
    for announcement in announcements:
        announcement["_id"] = str(announcement["_id"])
    
    # Sort by expiration_date descending (newest first)
    announcements.sort(key=lambda x: x.get("expiration_date", ""), reverse=True)
    
    return announcements


@router.post("")
def create_announcement(
    username: str,
    message: str,
    expiration_date: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new announcement (requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate expiration_date
    try:
        datetime.strptime(expiration_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid expiration_date format. Use YYYY-MM-DD"
        )
    
    # Validate start_date if provided
    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    
    # Create announcement document
    announcement = {
        "message": message,
        "expiration_date": expiration_date,
        "created_by": username,
        "created_at": datetime.now().isoformat()
    }
    
    if start_date:
        announcement["start_date"] = start_date
    
    # Insert into database
    result = announcements_collection.insert_one(announcement)
    
    # Return created announcement
    announcement["_id"] = str(result.inserted_id)
    return announcement


@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: str,
    username: str,
    message: str,
    expiration_date: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing announcement (requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate ObjectId
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    # Validate expiration_date
    try:
        datetime.strptime(expiration_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid expiration_date format. Use YYYY-MM-DD"
        )
    
    # Validate start_date if provided
    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    
    # Build update document
    update_doc = {
        "message": message,
        "expiration_date": expiration_date,
        "updated_by": username,
        "updated_at": datetime.now().isoformat()
    }
    
    if start_date:
        update_doc["start_date"] = start_date
    else:
        # Remove start_date if not provided
        announcements_collection.update_one(
            {"_id": obj_id},
            {"$unset": {"start_date": ""}}
        )
    
    # Update in database
    result = announcements_collection.update_one(
        {"_id": obj_id},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Return updated announcement
    updated_announcement = announcements_collection.find_one({"_id": obj_id})
    updated_announcement["_id"] = str(updated_announcement["_id"])
    return updated_announcement


@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: str, username: str) -> Dict[str, str]:
    """Delete an announcement (requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate ObjectId
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    # Delete from database
    result = announcements_collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    return {"message": "Announcement deleted successfully"}
