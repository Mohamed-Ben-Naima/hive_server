# hive_server/schemas/short_comments.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# Import necessary schemas for nested responses
# Reusing PostAuthorResponse for consistency in user representation
from .posts import PostAuthorResponse 

# --- Request Schemas ---
class ShortCommentCreate(BaseModel):
    """
    Schema for creating a new short comment.
    Requires the short_id and the text content of the comment.
    User ID will be derived from the authenticated user.
    """
    short_id: int = Field(..., description="The ID of the short the comment belongs to.")
    text_content: str = Field(..., min_length=1, max_length=500, description="The text content of the comment.")

    class Config:
        json_schema_extra = {
            "example": {
                "short_id": 456,
                "text_content": "Awesome short! Very informative."
            }
        }
        extra = "forbid" # Disallow extra fields in input

class ShortCommentUpdate(BaseModel):
    """
    Schema for updating an existing short comment.
    Only allows updating the text content.
    """
    text_content: str = Field(..., min_length=1, max_length=500, description="The updated text content of the comment.")

    class Config:
        json_schema_extra = {
            "example": {
                "text_content": "Revised comment after re-watching."
            }
        }
        extra = "forbid" # Disallow extra fields in input

# --- Response Schemas ---
class ShortCommentResponse(BaseModel):
    """
    Schema for returning short comment data in API responses.
    Includes comment details and information about the user who made the comment.
    """
    comment_id: int
    short_id: int
    user_id: int # Include user_id directly for clarity
    text_content: str
    created_at: datetime

    # Nested user information for the user who made the comment
    user: PostAuthorResponse # Reusing PostAuthorResponse for consistency

    class Config:
        from_attributes = True # Enable Pydantic to read from ORM object attributes
        populate_by_name = True # Allow population by field name or alias
        json_schema_extra = {
            "example": {
                "comment_id": 201,
                "short_id": 456,
                "user_id": 789,
                "text_content": "This is a great point!",
                "created_at": "2023-10-27T17:00:00Z",
                "user": {
                    "user_id": 789,
                    "email": "commenter@example.com",
                    "username": "ShortCommenter"
                }
            }
        }
