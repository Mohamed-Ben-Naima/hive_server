# hive_server/schemas/shorts.py

from pydantic import BaseModel, Field, HttpUrl, computed_field
from datetime import datetime
from typing import Optional, List
import os
import logging

logger = logging.getLogger("tea_n_hive_logger.shorts_schemas")

# Import necessary schemas for nested responses
# We need PostAuthorResponse to show who made the short
from .posts import PostAuthorResponse # Reusing PostAuthorResponse for consistency

# --- Request Schemas ---
class ShortCreate(BaseModel):
    """
    Schema for creating a new short video post.
    Requires a video file (handled by FastAPI's UploadFile) and an optional description.
    """
    description: Optional[str] = Field(None, max_length=500, description="Optional text description or caption for the short.")

    class Config:
        json_schema_extra = {
            "example": {
                "description": "My latest trading insights in 60 seconds!"
            }
        }
        extra = "forbid" # Disallow extra fields in input

class ShortUpdate(BaseModel):
    """
    Schema for updating an existing short video post.
    Allows updating the description. Video file updates will be handled separately.
    """
    description: Optional[str] = Field(None, max_length=500, description="The updated text description or caption for the short.")

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Updated insights on market volatility."
            }
        }
        extra = "forbid" # Disallow extra fields in input

# --- Response Schemas ---
class ShortResponse(BaseModel):
    """
    Schema for returning short video post data in API responses.
    Includes short details, author information, and aggregated counts for likes and comments.
    """
    short_id: int
    user_id: int # Include user_id directly for clarity
    description: Optional[str]
    created_at: datetime
    
    video_filename: str = Field(..., alias="video_url") # Internal filename, aliased from ORM

    user: PostAuthorResponse # Reusing PostAuthorResponse for consistency

    # Fields for likes count and user's like status
    likes_count: int = Field(0, description="Total number of likes for this short.")
    is_liked_by_current_user: bool = Field(False, description="True if the current authenticated user has liked this short.")
    
    # Field for comments count
    comments_count: int = Field(0, description="Total number of comments for this short.")

    @computed_field
    @property
    def video_url(self) -> HttpUrl:
        """
        Generates the full URL for the video file based on BASE_URL and media_filename.
        """
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        # Shorts videos will also be served from the /uploads directory
        return HttpUrl(f"{base_url}/uploads/{self.video_filename}")

    class Config:
        from_attributes = True # Enable Pydantic to read from ORM object attributes
        populate_by_name = True # Allow population by field name or alias
        json_schema_extra = {
            "examples": [
                {
                    "short_id": 1,
                    "user_id": 10,
                    "description": "Quick market update for today!",
                    "created_at": "2023-10-27T15:00:00Z",
                    "video_url": "http://localhost:8000/uploads/short_video_abc.mp4",
                    "user": {
                        "user_id": 10,
                        "email": "shortcreator@example.com",
                        "username": "ShortGuru"
                    },
                    "likes_count": 25,
                    "is_liked_by_current_user": True,
                    "comments_count": 8
                }
            ]
        }
