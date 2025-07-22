# hive_server/schemas/posts.py

from pydantic import BaseModel, Field, HttpUrl, EmailStr, computed_field
from datetime import datetime
from typing import Optional, List, Literal
import os
import logging

logger = logging.getLogger("tea_n_hive_logger.posts_schemas")

# --- NEW: Nested Schema for Profile Data within PostAuthorResponse ---
class ProfileForPostAuthor(BaseModel):
    username: str

    class Config:
        from_attributes = True # Allows this nested schema to be built from SQLAlchemy Profile object

# --- Specific User Response Schema for Post Author ---
class PostAuthorResponse(BaseModel):
    user_id: int
    email: EmailStr = Field(..., example="author@example.com", description="Author's email address.")
    
    # <--- MODIFIED: Now explicitly includes an optional 'profile' of type ProfileForPostAuthor ---
    profile: Optional[ProfileForPostAuthor] = None

    @computed_field
    @property
    def username(self) -> str:
        """
        Retrieves the username from the explicitly nested 'profile' field.
        This relies on the 'profile' relationship being eager-loaded by the service.
        """
        if self.profile and self.profile.username:
            return self.profile.username
        
        logger.warning(f"User ID {self.user_id} has no profile or username loaded for PostAuthorResponse. Defaulting to 'Unknown User'.")
        return "Unknown User" # Fallback for robustness

    class Config:
        from_attributes = True
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "email": "author@example.com",
                "username": "PostAuthor"
            }
        }

# --- Base Schemas for Requests (Posts Only) ---
class PostCreate(BaseModel):
    post_type: Literal["TEXT", "IMAGE", "VIDEO"] = Field(..., example="TEXT", description="Type of the post (e.g., TEXT, IMAGE, VIDEO).")
    text_content: Optional[str] = Field(None, max_length=1000, example="My thoughts on today's market trends.", description="Main text content of the post.")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "post_type": "TEXT",
                    "text_content": "Just closed a profitable trade on EUR/USD! Stay disciplined, folks."
                },
                {
                    "post_type": "IMAGE",
                    "text_content": "Chart analysis for tomorrow's session."
                },
                {
                    "post_type": "VIDEO"
                }
            ]
        }
        extra = "forbid"

class PostUpdate(BaseModel):
    post_type: Optional[Literal["TEXT", "IMAGE", "VIDEO"]] = Field(None, description="Optional new type of the post.")
    text_content: Optional[str] = Field(None, max_length=1000, example="Updated thoughts on the market.", description="Updated text content of the post.")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "text_content": "Revised analysis after new data release."
                },
                {
                    "post_type": "IMAGE",
                    "text_content": "Updated text for image post."
                }
            ]
        }
        extra = "forbid"

# --- Response Schemas (Posts Only) ---
class PostResponse(BaseModel):
    post_id: int
    user_id: int
    post_type: Literal["TEXT", "IMAGE", "VIDEO"]
    text_content: Optional[str]
    created_at: datetime

    media_filename: Optional[str] = Field(None, alias="media_url")

    user: PostAuthorResponse

    @computed_field
    @property
    def media_url(self) -> Optional[HttpUrl]:
        if self.media_filename:
            base_url = os.getenv("BASE_URL", "http://localhost:8000")
            return HttpUrl(f"{base_url}/uploads/{self.media_filename}")
        return None

    class Config:
        from_attributes = True
        populate_by_name = True
        json_schema_extra = {
            "examples": [
                {
                    "post_id": 101,
                    "user_id": 1,
                    "post_type": "TEXT",
                    "text_content": "My first post on Tea & Hive! Excited to share my trading journey.",
                    "media_url": None,
                    "created_at": "2023-10-27T10:00:00Z",
                    "user": {
                        "user_id": 1,
                        "email": "trader@example.com",
                        "username": "ProTrader"
                    }
                },
                {
                    "post_id": 102,
                    "user_id": 2,
                    "post_type": "IMAGE",
                    "text_content": "Check out this chart!",
                    "media_url": "http://localhost:8000/uploads/chart_xyz123.png",
                    "created_at": "2023-10-27T11:00:00Z",
                    "user": {
                        "user_id": 2,
                        "email": "analyst@example.com",
                        "username": "ChartMaster"
                    }
                }
            ]
        }
