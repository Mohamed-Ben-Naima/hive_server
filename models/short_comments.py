# hive_server/models/short_comments.py

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base # Relative import within the models package

class ShortComment(Base):
    __tablename__ = "short_comments" # Maps to the 'short_comments' table in the database

    comment_id = Column(Integer, primary_key=True, index=True)
    short_id = Column(Integer, ForeignKey("shorts.short_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    text_content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    # Many-to-one relationship with Short
    # back_populates will be set in shorts.py
    short = relationship("Short", back_populates="short_comments")
    
    # Many-to-one relationship with User (the commenter)
    # back_populates will be set in user.py
    user = relationship("User", back_populates="short_comments")

    def __repr__(self):
        return f"<ShortComment(comment_id={self.comment_id}, short_id={self.short_id}, user_id={self.user_id})>"
