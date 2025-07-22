# hive_server/services/post_likes.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import logging
from typing import List, Optional

logger = logging.getLogger("tea_n_hive_logger.post_likes_service")

from ..models import post_likes as post_likes_model
from ..models import posts as posts_model # To check if post exists
from ..models import user as user_model # To check if user exists and eager load for response
from ..schemas import post_likes as post_likes_schema

class PostLikesService:
    def __init__(self, db: Session):
        self.db = db

    def like_post(self, user_id: int, post_id: int) -> post_likes_model.PostLike:
        """
        Records a like for a post by a user.
        Raises HTTPException if the post or user does not exist, or if already liked.
        """
        logger.info(f"Attempting to like post ID: {post_id} by user ID: {user_id}.")

        # 1. Verify Post Existence
        post_exists = self.db.query(posts_model.Post).filter(posts_model.Post.post_id == post_id).first()
        if not post_exists:
            logger.warning(f"Like creation failed: Post ID {post_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found."
            )
        
        # 2. Verify User Existence (though current_user from dependency usually ensures this)
        user_exists = self.db.query(user_model.User).filter(user_model.User.user_id == user_id).first()
        if not user_exists:
            logger.warning(f"Like creation failed: User ID {user_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        # 3. Create the Like record
        db_like = post_likes_model.PostLike(
            user_id=user_id,
            post_id=post_id
        )
        try:
            self.db.add(db_like)
            self.db.commit()
            self.db.refresh(db_like) # Refresh to get like_id and created_at

            # Eager load user and profile for the response schema, ensuring created_at is loaded
            final_db_like = self.db.query(post_likes_model.PostLike)\
                .options(joinedload(post_likes_model.PostLike.user).joinedload(user_model.User.profile))\
                .filter(post_likes_model.PostLike.like_id == db_like.like_id)\
                .first()
            
            if not final_db_like: # Should not happen if commit was successful
                logger.error(f"Failed to retrieve newly created like ID: {db_like.like_id} after creation.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve like for response."
                )

            logger.info(f"Successfully liked post ID: {post_id} by user ID: {user_id}. Like ID: {final_db_like.like_id}.")
            return final_db_like
        except IntegrityError:
            self.db.rollback()
            logger.warning(f"User ID {user_id} already liked post ID {post_id}.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already liked this post."
            )
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Failed to like post ID: {post_id} by user ID: {user_id}. Rolling back transaction.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to like post due to a server error: {e}"
            )

    def unlike_post(self, user_id: int, post_id: int) -> None:
        """
        Removes a like from a post by a user.
        Raises HTTPException if the like does not exist.
        """
        logger.info(f"Attempting to unlike post ID: {post_id} by user ID: {user_id}.")
        db_like = self.db.query(post_likes_model.PostLike)\
            .filter(post_likes_model.PostLike.user_id == user_id, post_likes_model.PostLike.post_id == post_id)\
            .first()

        if not db_like:
            logger.warning(f"Unlike failed: User ID {user_id} has not liked post ID {post_id}.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Like not found (user has not liked this post)."
            )
        
        try:
            self.db.delete(db_like)
            self.db.commit()
            logger.info(f"Successfully unliked post ID: {post_id} by user ID: {user_id}.")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Failed to unlike post ID: {post_id} by user ID: {user_id}. Rolling back transaction.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to unlike post due to a server error: {e}"
            )

    def get_likes_for_post(self, post_id: int, skip: int = 0, limit: int = 10) -> List[post_likes_model.PostLike]:
        """
        Retrieves a paginated list of likes for a specific post, with liker's user and profile eager-loaded.
        """
        logger.debug(f"Attempting to retrieve likes for post ID: {post_id} (skip: {skip}, limit: {limit}).")
        likes = self.db.query(post_likes_model.PostLike)\
            .options(joinedload(post_likes_model.PostLike.user).joinedload(user_model.User.profile))\
            .filter(post_likes_model.PostLike.post_id == post_id)\
            .order_by(post_likes_model.PostLike.created_at.desc()) \
            .offset(skip)\
            .limit(limit)\
            .all()
        
        logger.debug(f"Successfully retrieved {len(likes)} likes for post ID: {post_id}.")
        return likes

    def get_posts_liked_by_user(self, user_id: int, skip: int = 0, limit: int = 10) -> List[post_likes_model.PostLike]:
        """
        Retrieves a paginated list of posts liked by a specific user, with liker's user and profile eager-loaded.
        """
        logger.debug(f"Attempting to retrieve posts liked by user ID: {user_id} (skip: {skip}, limit: {limit}).")
        likes = self.db.query(post_likes_model.PostLike)\
            .options(joinedload(post_likes_model.PostLike.user).joinedload(user_model.User.profile))\
            .filter(post_likes_model.PostLike.user_id == user_id)\
            .order_by(post_likes_model.PostLike.created_at.desc()) \
            .offset(skip)\
            .limit(limit)\
            .all()
        
        logger.debug(f"Successfully retrieved {len(likes)} liked posts for user ID: {user_id}.")
        return likes

    def get_like_status(self, user_id: int, post_id: int) -> bool:
        """
        Checks if a specific user has liked a specific post.
        """
        logger.debug(f"Checking like status for user ID: {user_id} on post ID: {post_id}.")
        like = self.db.query(post_likes_model.PostLike)\
            .filter(post_likes_model.PostLike.user_id == user_id, post_likes_model.PostLike.post_id == post_id)\
            .first()
        return like is not None
