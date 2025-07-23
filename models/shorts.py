# hive_server/models/shorts.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base # Relative import within the models package

class Short(Base):
    __tablename__ = "shorts" # Maps to the 'shorts' table in the database

    short_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    video_url = Column(String(255), nullable=False, comment="URL or path to the short video file")
    description = Column(Text, nullable=True, comment="Optional text description or caption for the short")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    # Many-to-one relationship with User (the author of the short)
    user = relationship("User", back_populates="shorts")

    # One-to-many relationship with ShortLike
    # cascade="all, delete-orphan" ensures that if a short is deleted,
    # all its associated likes are automatically deleted from the database.
    short_likes = relationship("ShortLike", back_populates="short", cascade="all, delete-orphan")

    # One-to-many relationship with ShortComment
    # cascade="all, delete-orphan" ensures that if a short is deleted,
    # all its associated comments are automatically deleted from the database.
    short_comments = relationship("ShortComment", back_populates="short", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Short(short_id={self.short_id}, user_id={self.user_id}, video_url='{self.video_url[:30]}...')>"
