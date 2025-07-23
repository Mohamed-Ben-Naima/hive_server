# hive_server/schemas/short_likes.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# Import necessary schemas for nested responses
# Reusing PostAuthorResponse for consistency in user representation
from .posts import PostAuthorResponse 

# --- Request Schemas ---
class ShortLikeCreate(BaseModel):
    """
    Schema for creating a new short like.
    Only requires the short_id, as user_id will be derived from the authenticated user.
    """
    short_id: int = Field(..., description="The ID of the short being liked.")

    class Config:
        json_schema_extra = {
            "example": {
                "short_id": 456
            }
        }
        extra = "forbid" # Disallow extra fields in input

# --- Response Schemas ---
class ShortLikeResponse(BaseModel):
    """
    Schema for returning short like data in API responses.
    Includes the like_id, associated short_id, details of the user who liked it, and created_at timestamp.
    """
    like_id: int
    short_id: int
    user_id: int # Include user_id directly for clarity
    created_at: datetime # Timestamp for when the like was created

    # Nested user information for the user who performed the like
    user: PostAuthorResponse # Reusing PostAuthorResponse for consistency

    class Config:
        from_attributes = True # Enable Pydantic to read from ORM object attributes
        populate_by_name = True # Allow population by field name or alias
        json_schema_extra = {
            "example": {
                "like_id": 101,
                "short_id": 456,
                "user_id": 789,
                "created_at": "2023-10-27T16:00:00Z",
                "user": {
                    "user_id": 789,
                    "email": "shortliker@example.com",
                    "username": "ShortFan"
                }
            }
        }
