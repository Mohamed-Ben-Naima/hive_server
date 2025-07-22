# hive_server/models/posts.py

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base # Import Base from your existing base.py

# No direct import of User model here to prevent potential circular import issues.
# Relationships will use string literals, resolved by Base.registry.configure() in app_setup.py.

class Post(Base):
    __tablename__ = "posts"

    post_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    post_type = Column(String(50), nullable=False, comment="Type of post: 'TEXT', 'IMAGE', 'VIDEO', etc.") # Matches SQL
    text_content = Column(Text, nullable=True, comment="Main text content of the post") # Matches SQL
    media_url = Column(String(255), nullable=True, comment="URL to media (image/video) associated with the post") # Matches SQL
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) # Matches SQL
    # Note: SQL schema does not have 'updated_at' for posts, so we omit it here for strict alignment.

    # Relationships - Using string literal for "User" (resolved by Base.registry.configure())
    user = relationship("User", back_populates="posts")
    # Note: comments and likes relationships will be added later when we develop those models.
    # comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    # likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Post(post_id={self.post_id}, user_id={self.user_id}, type='{self.post_type}', content='{self.text_content[:30] if self.text_content else ''}...')>"

# Note: Comment and Like models will be added to this file later.
# class Comment(Base): ...
# class Like(Base): ...
