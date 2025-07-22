# hive_server/models/post_comments.py

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base # Relative import within the models package

class PostComment(Base):
    __tablename__ = "post_comments" # Maps to the 'post_comments' table in the database

    comment_id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.post_id", ondelete="CASCADE"), nullable=False, index=True) # Add index for faster lookups
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True) # Add index for faster lookups
    text_content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    # Many-to-one relationship with Post
    # back_populates will be set in posts.py
    post = relationship("Post", back_populates="post_comments")
    
    # Many-to-one relationship with User (the commenter)
    # back_populates will be set in user.py
    user = relationship("User", back_populates="post_comments")

    def __repr__(self):
        return f"<PostComment(comment_id={self.comment_id}, post_id={self.post_id}, user_id={self.user_id})>"
