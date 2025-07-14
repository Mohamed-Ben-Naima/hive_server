# Hive-server/schemas/user.py

from pydantic import BaseModel, EmailStr, Field, ValidationError
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    """Pydantic model for user registration input."""
    email: EmailStr = Field(..., example="user@example.com", description="User's email address.")
    password: str = Field(..., min_length=8, max_length=255, example="SecureP@ssw0rd", description="User's password.")
    verify_password: str = Field(..., example="SecureP@ssw0rd", description="Password confirmation.")

    # Pydantic validator to ensure passwords match before processing
    def model_post_init(self, __context__):
        if self.password != self.verify_password:
            raise ValueError("Passwords do not match")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "email": "test@example.com",
                    "password": "Password123!",
                    "verify_password": "Password123!"
                }
            ]
        }
        extra = "forbid" # Disallow extra fields in the request body

class UserResponse(BaseModel):
    """Pydantic model for user data returned in API responses."""
    user_id: int = Field(..., description="Unique identifier for the user.")
    email: EmailStr = Field(..., example="user@example.com", description="User's email address.")
    created_at: datetime = Field(..., description="Timestamp of user creation.")
    last_login: Optional[datetime] = Field(None, description="Timestamp of user's last login.")

    class Config:
        from_attributes = True # Allow Pydantic to read attributes directly from SQLAlchemy models
        json_schema_extra = {
            "examples": [
                {
                    "user_id": 1,
                    "email": "test@example.com",
                    "created_at": "2023-10-27T10:00:00Z",
                    "last_login": "2023-10-27T10:00:00Z"
                }
            ]
        }