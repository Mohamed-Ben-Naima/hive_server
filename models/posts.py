# hive_server/models/posts.py

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base # Import Base from your existing base.py

class Post(Base):
    __tablename__ = "posts"

    post_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    post_type = Column(String(50), nullable=False, comment="Type of post: 'TEXT', 'IMAGE', 'VIDEO', etc.")
    text_content = Column(Text, nullable=True, comment="Main text content of the post")
    media_url = Column(String(255), nullable=True, comment="URL to media (image/video) associated with the post")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    # One-to-many relationship with User
    user = relationship("User", back_populates="posts")

    # One-to-many relationship with PostLike
    post_likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")

    # --- NEW: One-to-many relationship with PostComment ---
    # back_populates="post" links to the 'post' relationship in the PostComment model.
    # cascade="all, delete-orphan" ensures that if a post is deleted,
    # all its associated comments are automatically deleted from the database.
    post_comments = relationship("PostComment", back_populates="post", cascade="all, delete-orphan")
    # --- END NEW ---

    def __repr__(self):
        return f"<Post(post_id={self.post_id}, user_id={self.user_id}, type='{self.post_type}', content='{self.text_content[:30] if self.text_content else ''}...')>"
