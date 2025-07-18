# Hive-server/schemas/user.py

from pydantic import BaseModel, EmailStr, Field, field_validator # <-- field_validator already imported
from datetime import datetime
from typing import Optional, Any
import re # <-- Ensure this is imported for regex

# Regex for strong password validation:
# At least 8 characters, one uppercase, one lowercase, one digit, one special character
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"

class UserCreate(BaseModel):
    email: EmailStr = Field(..., example="user@example.com", description="User's email address.")
    username: str = Field(..., min_length=3, max_length=50, example="TraderBee", description="Unique username for the user's profile.")
    password: str = Field(..., min_length=8, max_length=255, example="SecureP@ssw0rd1", description="User's password.")
    verify_password: str = Field(..., example="SecureP@ssw0rd1", description="Password confirmation.")

    @field_validator('username')
    @classmethod
    def validate_username(cls, value):
        if not value.strip():
            raise ValueError("Username cannot be empty or just spaces.")
        if " " in value:
            raise ValueError("Username cannot contain spaces.")
        return value.strip()

    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, value):
        if not re.match(PASSWORD_REGEX, value):
            raise ValueError(
                "Password must be at least 8 characters long and include "
                "at least one uppercase letter, one lowercase letter, one digit, and one special character."
            )
        return value

    @field_validator('verify_password')
    @classmethod
    def passwords_match(cls, v, values):
        password = values.data.get('password') if hasattr(values, 'data') else values.get('password')
        if password is not None and v != password:
            raise ValueError('Passwords do not match.')
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "email": "newuser@example.com",
                    "username": "NewBeeTrader",
                    "password": "StrongP@ss1",
                    "verify_password": "StrongP@ss1"
                }
            ]
        }
        extra = "forbid"

class ProfileResponse(BaseModel):
    profile_id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    trading_style: Optional[str] = None
    social_links: Optional[dict] = None

    class Config:
        from_attributes = True
        json_schema_extra = { # <-- NEW/UPDATED: Example for ProfileResponse
            "examples": [
                {
                    "profile_id": 1,
                    "username": "TestTrader",
                    "first_name": "John",
                    "last_name": "Doe",
                    "gender": "Male",
                    "avatar_url": "https://placehold.co/100x100/aabbcc/ffffff?text=Avatar",
                    "bio": "Experienced trader focusing on forex and commodities.",
                    "trading_style": "Swing Trading", # <-- UPDATED: Example value for trading_style
                    "social_links": {"twitter": "johndoe_trader", "linkedin": "johndoe"}
                }
            ]
        }

class UserResponse(BaseModel):
    user_id: int
    email: EmailStr
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = { # <-- NEW/UPDATED: Example for UserResponse
            "examples": [
                {
                    "user_id": 1,
                    "email": "test@example.com",
                    "created_at": "2023-10-27T10:00:00.123456", # More realistic ISO format
                    "last_login": "2023-10-27T10:00:00.123456"  # More realistic ISO format
                }
            ]
        }

class UserWithProfileResponse(UserResponse):
    profile: ProfileResponse
    message: Optional[str] = Field(None, description="A success message for the operation.") # <-- NEW: Optional success message

    class Config:
        from_attributes = True
        json_schema_extra = {
            "examples": [
                {
                    "user_id": 1,
                    "email": "test@example.com",
                    "created_at": "2023-10-27T10:00:00Z",
                    "last_login": "2023-10-27T10:00:00Z",
                    "profile": {
                        "profile_id": 1,
                        "username": "TestTrader",
                        "first_name": "John",
                        "last_name": "Doe",
                        "gender": "Male",
                        "avatar_url": "http://example.com/avatar.png",
                        "bio": "Experienced trader.",
                        "trading_style": "Scalping",
                        "social_links": {"twitter": "johndoe"}
                    },
                    "message": "User registered successfully!" # Example message
                }
            ]
        }

class UserForTokenResponse(BaseModel):
    user_id: int = Field(..., example=1)
    email: EmailStr = Field(..., example="user@example.com")
    username: str = Field(..., example="TraderBee") # Include username if available

    class Config:
        from_attributes = True
        json_schema_extra = {
            "examples": [
                {
                    "user_id": 1,
                    "email": "user@example.com",
                    "username": "TraderBee",
                }
            ]
        }

class ProfileUpdate(BaseModel):
    # All fields are Optional for PATCH requests
    username: Optional[str] = Field(None, min_length=3, max_length=50, example="UpdatedTraderBee", description="New unique username for the user's profile.")
    first_name: Optional[str] = Field(None, max_length=100, example="Jane", description="User's first name.")
    last_name: Optional[str] = Field(None, max_length=100, example="Smith", description="User's last name.")
    gender: Optional[str] = Field(None, max_length=20, example="Female", description="User's gender.")
    avatar_url: Optional[str] = Field(None, example="https://new-avatar.com/image.png", description="URL to the user's new avatar image.")
    bio: Optional[str] = Field(None, max_length=500, example="Passionate day trader focusing on crypto.", description="A short biography about the user.")
    trading_style: Optional[str] = Field(None, max_length=100, example="Day Trading", description="User's preferred trading style.")
    social_links: Optional[dict] = Field(None, example={"twitter": "janesmith_trade", "instagram": "janesmith.trading"}, description="A dictionary of social media links.")

    @field_validator('username')
    @classmethod
    def validate_username_update(cls, value):
        if value is not None: # Only validate if a value is provided
            if not value.strip():
                raise ValueError("Username cannot be empty or just spaces.")
            if " " in value:
                raise ValueError("Username cannot contain spaces.")
        return value.strip() if value else value # Strip spaces if not None

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "username": "NewTraderName",
                    "bio": "Updated bio for my profile.",
                    "trading_style": "Swing Trading"
                },
                {
                    "first_name": "Alice",
                    "last_name": "Wonder",
                    "gender": "Female"
                }
            ]
        }