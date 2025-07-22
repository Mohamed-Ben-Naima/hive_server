# hive_server/schemas/post_comments.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# Import necessary schemas for nested responses
# We need PostAuthorResponse to show who made the comment
from .posts import PostAuthorResponse 

# --- Request Schemas ---
class PostCommentCreate(BaseModel):
    """
    Schema for creating a new post comment.
    Requires the post_id and the text content of the comment.
    User ID will be derived from the authenticated user.
    """
    post_id: int = Field(..., description="The ID of the post the comment belongs to.")
    text_content: str = Field(..., min_length=1, max_length=500, description="The text content of the comment.")

    class Config:
        json_schema_extra = {
            "example": {
                "post_id": 123,
                "text_content": "Great post! Very insightful."
            }
        }
        extra = "forbid" # Disallow extra fields in input

class PostCommentUpdate(BaseModel):
    """
    Schema for updating an existing post comment.
    Only allows updating the text content.
    """
    text_content: str = Field(..., min_length=1, max_length=500, description="The updated text content of the comment.")

    class Config:
        json_schema_extra = {
            "example": {
                "text_content": "Updated my thoughts on this."
            }
        }
        extra = "forbid" # Disallow extra fields in input

# --- Response Schemas ---
class PostCommentResponse(BaseModel):
    """
    Schema for returning post comment data in API responses.
    Includes comment details and information about the user who made the comment.
    """
    comment_id: int
    post_id: int
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
                "comment_id": 1,
                "post_id": 123,
                "user_id": 456,
                "text_content": "This is a fantastic analysis!",
                "created_at": "2023-10-27T15:30:00Z",
                "user": {
                    "user_id": 456,
                    "email": "commenter@example.com",
                    "username": "CommentKing"
                }
            }
        }
