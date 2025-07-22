# hive_server/models/post_likes.py

from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base # Relative import within the models package

class PostLike(Base):
    __tablename__ = "post_likes" # Maps to the 'post_likes' table in the database

    like_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.post_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) # <--- THIS LINE MUST BE PRESENT!

    # Define unique constraint to prevent a user from liking the same post multiple times
    __table_args__ = (UniqueConstraint('post_id', 'user_id', name='_post_user_uc'),)

    # Relationships
    # Many-to-one relationship with User
    user = relationship("User", back_populates="post_likes")
    # Many-to-one relationship with Post
    post = relationship("Post", back_populates="post_likes")

    def __repr__(self):
        return f"<PostLike(like_id={self.like_id}, user_id={self.user_id}, post_id={self.post_id})>"
