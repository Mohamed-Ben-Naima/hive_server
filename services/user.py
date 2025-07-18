# Hive-server/services/user.py

from sqlalchemy.orm import Session, joinedload # <--- IMPORTANT: Ensure joinedload is imported
from fastapi import HTTPException, status
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger("tea_n_hive_logger.user_service")

from ..models import user as user_model
from ..schemas import user as user_schema
from ..utils import security

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[user_model.User]:
        logger.debug(f"Attempting to retrieve user by email: {email}")
        # <--- RE-ADDED: Eager load the profile
        return self.db.query(user_model.User).options(joinedload(user_model.User.profile)).filter(user_model.User.email == email).first()

    def get_profile_by_username(self, username: str) -> Optional[user_model.Profile]:
        logger.debug(f"Attempting to retrieve profile by username: {username}")
        # <--- RE-ADDED: Eager load the user (if profile.user is needed later)
        return self.db.query(user_model.Profile).options(joinedload(user_model.Profile.user)).filter(user_model.Profile.username == username).first()

    def get_user_by_id(self, user_id: int) -> Optional[user_model.User]:
        logger.debug(f"Attempting to retrieve user by ID: {user_id}")
        # <--- RE-ADDED: Eager load the profile
        return self.db.query(user_model.User).options(joinedload(user_model.User.profile)).filter(user_model.User.user_id == user_id).first()

    def create_user(self, user_data: user_schema.UserCreate) -> user_model.User:
        logger.info(f"Attempting to create new user: {user_data.email} with username: {user_data.username}")

        if self.get_user_by_email(user_data.email): # This now eager-loads the profile, which is fine
            logger.warning(f"Registration failed: Email already registered: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        if self.get_profile_by_username(user_data.username): # This now eager-loads the user, which is fine
            logger.warning(f"Registration failed: Username already taken: {user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken"
            )

        hashed_password = security.get_password_hash(user_data.password)

        try:
            db_user = user_model.User(
                email=user_data.email,
                password_hash=hashed_password
            )
            self.db.add(db_user)
            self.db.flush()

            db_profile = user_model.Profile(
                user_id=db_user.user_id,
                username=user_data.username,
                first_name=None, last_name=None, gender=None,
                avatar_url=None, bio=None, trading_style=None, social_links=None
            )
            self.db.add(db_profile)
            self.db.commit()
            self.db.refresh(db_user)
            self.db.refresh(db_profile)

            db_user.profile = db_profile # Ensure the profile relationship is loaded after creation

            logger.info(f"Successfully created user (ID: {db_user.user_id}, Email: {db_user.email}) and profile (ID: {db_profile.profile_id}, Username: {db_profile.username}).")
            return db_user
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Error during user and profile creation for {user_data.email}. Rolling back transaction.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user and profile due to a server error."
            )

    def authenticate_user(self, email_or_username: str, password: str) -> Optional[user_model.User]:
        logger.info(f"Attempting to authenticate user: {email_or_username}")
        
        # Try to find user by email, eager-loading profile
        user = self.db.query(user_model.User).options(joinedload(user_model.User.profile)).filter(user_model.User.email == email_or_username).first()
        
        # If not found by email, try to find by username (via profile), eager-loading user and then its profile
        if not user:
            profile = self.db.query(user_model.Profile).options(joinedload(user_model.Profile.user)).filter(user_model.Profile.username == email_or_username).first()
            if profile and profile.user: # Ensure profile and its user relationship exist
                user = profile.user # Use the eager-loaded user from the profile

        if not user or not security.verify_password(password, user.password_hash):
            logger.warning(f"Authentication failed for: {email_or_username}. Invalid credentials.")
            return None
        
        logger.info(f"User {email_or_username} authenticated successfully.")
        return user
    
    def update_user_last_login(self, user: user_model.User):
        """Updates the last_login timestamp for a given user."""
        try:
            user.last_login = datetime.utcnow()
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.debug(f"Updated last_login for user ID: {user.user_id}, Email: {user.email}")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Failed to update last_login for user ID: {user.user_id}. Rolling back.")

    def update_user_profile(self, user: user_model.User, profile_data: user_schema.ProfileUpdate) -> user_model.User:
        """
        Updates the profile of a given user with the provided data.
        Only updates fields that are explicitly provided in profile_data.
        """
        logger.info(f"Attempting to update profile for user ID: {user.user_id}, Email: {user.email}")

        if not user.profile:
            logger.error(f"User {user.user_id} has no associated profile to update.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found."
            )

        if profile_data.username is not None and profile_data.username != user.profile.username:
            existing_profile = self.get_profile_by_username(profile_data.username)
            if existing_profile and existing_profile.user_id != user.user_id:
                logger.warning(f"Profile update failed: New username '{profile_data.username}' already taken by another user.")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already taken by another user."
                )

        try:
            for field, value in profile_data.model_dump(exclude_unset=True).items():
                if field == "social_links" and isinstance(value, dict):
                    if user.profile.social_links is None:
                        user.profile.social_links = {}
                    user.profile.social_links.update(value)
                else:
                    setattr(user.profile, field, value)

            self.db.add(user.profile)
            self.db.commit()
            self.db.refresh(user.profile)
            self.db.refresh(user)

            logger.info(f"Successfully updated profile for user ID: {user.user_id}, Username: {user.profile.username}.")
            return user
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Error updating profile for user ID: {user.user_id}. Rolling back transaction.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update profile due to a server error: {e}"
            )