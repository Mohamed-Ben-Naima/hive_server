# Hive-server/services/user.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional
import logging # <-- NEW: Import logging

# Get logger instance for this module
logger = logging.getLogger("trader_hive_logger.user_service")

from ..models import user as user_model
from ..schemas import user as user_schema
from ..utils import security

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[user_model.User]:
        logger.debug(f"Attempting to retrieve user by email: {email}")
        return self.db.query(user_model.User).filter(user_model.User.email == email).first()

    def get_profile_by_username(self, username: str) -> Optional[user_model.Profile]:
        logger.debug(f"Attempting to retrieve profile by username: {username}")
        return self.db.query(user_model.Profile).filter(user_model.Profile.username == username).first()

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

            db_user.profile # Ensure relationship is loaded for response

            logger.info(f"Successfully created user (ID: {db_user.user_id}, Email: {db_user.email}) and profile (ID: {db_profile.profile_id}, Username: {db_profile.username}).")
            return db_user
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Error during user and profile creation for {user_data.email}. Rolling back transaction.") # logger.exception logs traceback
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user and profile due to a server error."
            )