# hive_server/models/short_likes.py

from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base # Relative import within the models package

class ShortLike(Base):
    __tablename__ = "short_likes" # Maps to the 'short_likes' table in the database

    like_id = Column(Integer, primary_key=True, index=True)
    short_id = Column(Integer, ForeignKey("shorts.short_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Define unique constraint to prevent a user from liking the same short multiple times
    # This directly enforces the business rule at the database level.
    __table_args__ = (UniqueConstraint('short_id', 'user_id', name='_short_user_uc'),)

    # Relationships
    # Many-to-one relationship with Short
    # back_populates will be set in shorts.py
    short = relationship("Short", back_populates="short_likes")
    
    # Many-to-one relationship with User (the liker)
    # back_populates will be set in user.py
    user = relationship("User", back_populates="short_likes")

    def __repr__(self):
        return f"<ShortLike(like_id={self.like_id}, short_id={self.short_id}, user_id={self.user_id})>"
