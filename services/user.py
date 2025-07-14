# Hive-server/services/user.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional

from ..models import user as user_model # Import User ORM model
from ..schemas import user as user_schema # Import UserCreate/UserResponse schemas
from ..utils import security # Import security utilities for password hashing

class UserService:
    """
    Handles all business logic related to user management.
    Interacts with the database via SQLAlchemy models.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[user_model.User]:
        """Retrieves a user by their email address from the database."""
        return self.db.query(user_model.User).filter(user_model.User.email == email).first()

    def create_user(self, user_data: user_schema.UserCreate) -> user_model.User:
        """
        Creates a new user in the database after hashing the password.
        Raises HTTPException if email is already registered.
        """
        # Check if user with this email already exists to prevent duplicates
        if self.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        # Hash the plain-text password before storing it
        hashed_password = security.get_password_hash(user_data.password)

        # Create a new User ORM object
        db_user = user_model.User(
            email=user_data.email,
            password_hash=hashed_password
            # created_at and last_login will be handled by database defaults or SQLAlchemy
        )

        # Add the new user to the session, commit, and refresh to get database-generated fields
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user) # Refresh to load user_id and created_at from DB
        return db_user

    # Future: Add methods for login, update user profile, delete user, etc.