# Hive-server/services/user.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional
import logging
from datetime import datetime 

logger = logging.getLogger("tea_n_hive_logger.user_service") # Corrected logger name

from ..models import user as user_model # Relative import
from ..schemas import user as user_schema # Relative import
from ..utils import security # Relative import

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[user_model.User]:
        logger.debug(f"Attempting to retrieve user by email: {email}")
        return self.db.query(user_model.User).filter(user_model.User.email == email).first()

    def get_profile_by_username(self, username: str) -> Optional[user_model.Profile]:
        logger.debug(f"Attempting to retrieve profile by username: {username}")
        return self.db.query(user_model.Profile).filter(user_model.Profile.username == username).first()

    def get_user_by_id(self, user_id: int) -> Optional[user_model.User]:
        logger.debug(f"Attempting to retrieve user by ID: {user_id}")
        return self.db.query(user_model.User).filter(user_model.User.user_id == user_id).first()

    def create_user(self, user_data: user_schema.UserCreate) -> user_model.User:
        logger.info(f"Attempting to create new user: {user_data.email} with username: {user_data.username}")

        if self.get_user_by_email(user_data.email):
            logger.warning(f"Registration failed: Email already registered: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        if self.get_profile_by_username(user_data.username):
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

            db_user.profile

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
        user = self.db.query(user_model.User).filter(user_model.User.email == email_or_username).first()
        if not user:
            profile = self.db.query(user_model.Profile).filter(user_model.Profile.username == email_or_username).first()
            if profile:
                user = self.db.query(user_model.User).filter(user_model.User.user_id == profile.user_id).first()

        if not user or not security.verify_password(password, user.password_hash):
            logger.warning(f"Authentication failed for: {email_or_username}. Invalid credentials.")
            return None
        
        logger.info(f"User {email_or_username} authenticated successfully.")
        return user
    
    # <--- NEW: Method to update last_login timestamp ---
    def update_user_last_login(self, user: user_model.User):
        """Updates the last_login timestamp for a given user."""
        try:
            user.last_login = datetime.utcnow() # Set to current UTC time
            self.db.add(user) # Add to session (or merge if detached)
            self.db.commit() # Commit the change
            self.db.refresh(user) # Refresh the user object to reflect changes
            logger.debug(f"Updated last_login for user ID: {user.user_id}, Email: {user.email}")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Failed to update last_login for user ID: {user.user_id}. Rolling back.")