# Hive-server/models/user.py

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base # Relative import within the models package

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # One-to-one relationship with Profile
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # One-to-many relationship with Posts
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")

    # One-to-many relationship with PostLike
    post_likes = relationship("PostLike", back_populates="user", cascade="all, delete-orphan")

    # One-to-many relationship with PostComment
    post_comments = relationship("PostComment", back_populates="user", cascade="all, delete-orphan")

    # --- NEW: One-to-many relationship with Short ---
    # back_populates="user" links to the 'user' relationship in the Short model.
    # cascade="all, delete-orphan" ensures that if a user is deleted,
    # all their associated shorts are automatically deleted from the database.
    shorts = relationship("Short", back_populates="user", cascade="all, delete-orphan")
    # --- END NEW ---

    # --- NEW: One-to-many relationship with ShortLike ---
    # back_populates="user" links to the 'user' relationship in the ShortLike model.
    # cascade="all, delete-orphan" ensures that if a user is deleted,
    # all their associated short likes are automatically deleted from the database.
    short_likes = relationship("ShortLike", back_populates="user", cascade="all, delete-orphan")
    # --- END NEW ---

    # --- NEW: One-to-many relationship with ShortComment ---
    # back_populates="user" links to the 'user' relationship in the ShortComment model.
    # cascade="all, delete-orphan" ensures that if a user is deleted,
    # all their associated short comments are automatically deleted from the database.
    short_comments = relationship("ShortComment", back_populates="user", cascade="all, delete-orphan")
    # --- END NEW ---
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, email='{self.email}')>"

class Profile(Base):
    __tablename__ = "profiles"

    profile_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    gender = Column(String(50), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    trading_style = Column(String(100), nullable=True)
    social_links = Column(JSONB, nullable=True)

    # One-to-one relationship with User
    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<Profile(profile_id={self.profile_id}, username='{self.username}')>"
