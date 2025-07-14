# Hive-server/models/user.py

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .base import Base # Relative import for Base from models.base

class User(Base):
    __tablename__ = "users" # Maps to the "users" table in your PostgreSQL schema

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # You can define relationships to other models (e.g., Profile) here later.
    # Example: profiles = relationship("Profile", back_populates="user")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, email='{self.email}')>"