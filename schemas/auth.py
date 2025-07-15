# hive_server/schemas/auth.py

from pydantic import BaseModel, Field
from typing import Optional

from ..schemas.user import UserForTokenResponse 

# Schema for the JWT token returned upon successful authentication
class Token(BaseModel):
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field("bearer", example="bearer")
    user: Optional[UserForTokenResponse] = None # <--- CHANGED: Now uses UserForTokenResponse

# Schema for the data contained within the JWT token (payload)
class TokenData(BaseModel):
    user_id: int | None = None # Use Optional[int] for older Python versions
    email: str | None = None # Add email for easier debugging/logging if needed

