# hive_server/schemas/post_likes.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# Import necessary schemas for nested responses
# We need PostAuthorResponse to show who liked the post
from .posts import PostAuthorResponse 

# --- Request Schemas ---
class PostLikeCreate(BaseModel):
    """
    Schema for creating a new post like.
    Only requires the post_id, as user_id will be derived from the authenticated user.
    """
    post_id: int = Field(..., description="The ID of the post being liked.")

    class Config:
        json_schema_extra = {
            "example": {
                "post_id": 123
            }
        }
        extra = "forbid" # Disallow extra fields in input

# --- Response Schemas ---
class PostLikeResponse(BaseModel):
    """
    Schema for returning post like data in API responses.
    Includes the like_id, associated post_id, and details of the user who liked it.
    """
    like_id: int
    post_id: int
    user_id: int # Include user_id directly for clarity
    # Note: 'created_at' is omitted here to match your SQL schema for post_likes,
    # which does not have a created_at column. If you add it to SQL, add it here too.
    # created_at: datetime

    # Nested user information for the user who performed the like
    user: PostAuthorResponse # Reusing PostAuthorResponse for consistency

    class Config:
        from_attributes = True # Enable Pydantic to read from ORM object attributes
        populate_by_name = True # Allow population by field name or alias
        json_schema_extra = {
            "example": {
                "like_id": 1,
                "post_id": 123,
                "user_id": 456,
                "user": {
                    "user_id": 456,
                    "email": "liker@example.com",
                    "username": "LikeMaster"
                }
                # "created_at": "2023-10-27T15:30:00Z" # If you add created_at to SQL
            }
        }
