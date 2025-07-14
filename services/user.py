# Hive-server/services/user.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional

from ..models import user as user_model
from ..schemas import user as user_schema
from ..utils import security

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[user_model.User]:
        return self.db.query(user_model.User).filter(user_model.User.email == email).first()

    def get_profile_by_username(self, username: str) -> Optional[user_model.Profile]: # <-- NEW: Check username uniqueness
        return self.db.query(user_model.Profile).filter(user_model.Profile.username == username).first()

    def create_user(self, user_data: user_schema.UserCreate) -> user_model.User: # Return User object
        # Check if email already registered
        if self.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        # Check if username already taken
        if self.get_profile_by_username(user_data.username): # <-- NEW: Check username
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken"
            )

        hashed_password = security.get_password_hash(user_data.password)

        # Create User and Profile within a transaction
        try:
            db_user = user_model.User(
                email=user_data.email,
                password_hash=hashed_password
            )
            self.db.add(db_user)
            self.db.flush() # Flush to get user_id before creating profile

            db_profile = user_model.Profile( # <-- NEW: Create Profile
                user_id=db_user.user_id,
                username=user_data.username,
                # Default values for other profile fields (can be updated later)
                first_name=None,
                last_name=None,
                gender=None,
                avatar_url=None,
                bio=None,
                trading_style=None,
                social_links=None
            )
            self.db.add(db_profile)
            self.db.commit()
            self.db.refresh(db_user) # Refresh user to load its 'profile' relationship
            self.db.refresh(db_profile) # Refresh profile to load its profile_id

            # Ensure the relationship is loaded for the response
            db_user.profile # Accessing it ensures it's loaded

            return db_user
        except Exception as e:
            self.db.rollback() # Rollback transaction on error
            print(f"Error during user and profile creation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user and profile due to a server error."
            )