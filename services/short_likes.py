# hive_server/services/short_likes.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import logging
from typing import List, Optional

logger = logging.getLogger("tea_n_hive_logger.short_likes_service")

from ..models import short_likes as short_likes_model
from ..models import shorts as shorts_model # To check if short exists
from ..models import user as user_model # To check if user exists and eager load for response
from ..schemas import short_likes as short_likes_schema

class ShortLikesService:
    def __init__(self, db: Session):
        self.db = db

    def like_short(self, user_id: int, short_id: int) -> short_likes_model.ShortLike:
        """
        Records a like for a short by a user.
        Raises HTTPException if the short or user does not exist, or if already liked.
        """
        logger.info(f"Attempting to like short ID: {short_id} by user ID: {user_id}.")

        # 1. Verify Short Existence
        short_exists = self.db.query(shorts_model.Short).filter(shorts_model.Short.short_id == short_id).first()
        if not short_exists:
            logger.warning(f"Like creation failed: Short ID {short_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short not found."
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
        db_like = short_likes_model.ShortLike(
            user_id=user_id,
            short_id=short_id
        )
        try:
            self.db.add(db_like)
            self.db.commit()
            self.db.refresh(db_like) # Refresh to get like_id and created_at

            # Eager load user and profile for the response schema
            final_db_like = self.db.query(short_likes_model.ShortLike)\
                .options(joinedload(short_likes_model.ShortLike.user).joinedload(user_model.User.profile))\
                .filter(short_likes_model.ShortLike.like_id == db_like.like_id)\
                .first()
            
            if not final_db_like: # Should not happen if commit was successful
                logger.error(f"Failed to retrieve newly created like ID: {db_like.like_id} after creation.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve like for response."
                )

            logger.info(f"Successfully liked short ID: {short_id} by user ID: {user_id}. Like ID: {final_db_like.like_id}.")
            return final_db_like
        except IntegrityError:
            self.db.rollback()
            logger.warning(f"User ID {user_id} already liked short ID {short_id}.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already liked this short."
            )
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Failed to like short ID: {short_id} by user ID: {user_id}. Rolling back transaction.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to like short due to a server error: {e}"
            )

    def unlike_short(self, user_id: int, short_id: int) -> None:
        """
        Removes a like from a short by a user.
        Raises HTTPException if the like does not exist.
        """
        logger.info(f"Attempting to unlike short ID: {short_id} by user ID: {user_id}.")
        db_like = self.db.query(short_likes_model.ShortLike)\
            .filter(short_likes_model.ShortLike.user_id == user_id, short_likes_model.ShortLike.short_id == short_id)\
            .first()

        if not db_like:
            logger.warning(f"Unlike failed: User ID {user_id} has not liked short ID {short_id}.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Like not found (user has not liked this short)."
            )
        
        try:
            self.db.delete(db_like)
            self.db.commit()
            logger.info(f"Successfully unliked short ID: {short_id} by user ID: {user_id}.")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Failed to unlike short ID: {short_id} by user ID: {user_id}. Rolling back transaction.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to unlike short due to a server error: {e}"
            )

    def get_likes_for_short(self, short_id: int, skip: int = 0, limit: int = 10) -> List[short_likes_model.ShortLike]:
        """
        Retrieves a paginated list of likes for a specific short, with liker's user and profile eager-loaded.
        """
        logger.debug(f"Attempting to retrieve likes for short ID: {short_id} (skip: {skip}, limit: {limit}).")
        likes = self.db.query(short_likes_model.ShortLike)\
            .options(joinedload(short_likes_model.ShortLike.user).joinedload(user_model.User.profile))\
            .filter(short_likes_model.ShortLike.short_id == short_id)\
            .order_by(short_likes_model.ShortLike.created_at.desc()) \
            .offset(skip)\
            .limit(limit)\
            .all()
        
        logger.debug(f"Successfully retrieved {len(likes)} likes for short ID: {short_id}.")
        return likes

    def get_shorts_liked_by_user(self, user_id: int, skip: int = 0, limit: int = 10) -> List[short_likes_model.ShortLike]:
        """
        Retrieves a paginated list of shorts liked by a specific user, with liker's user and profile eager-loaded.
        """
        logger.debug(f"Attempting to retrieve shorts liked by user ID: {user_id} (skip: {skip}, limit: {limit}).")
        likes = self.db.query(short_likes_model.ShortLike)\
            .options(joinedload(short_likes_model.ShortLike.user).joinedload(user_model.User.profile))\
            .filter(short_likes_model.ShortLike.user_id == user_id)\
            .order_by(short_likes_model.ShortLike.created_at.desc()) \
            .offset(skip)\
            .limit(limit)\
            .all()
        
        logger.debug(f"Successfully retrieved {len(likes)} liked shorts for user ID: {user_id}.")
        return likes

    def get_like_status(self, user_id: int, short_id: int) -> bool:
        """
        Checks if a specific user has liked a specific short.
        """
        logger.debug(f"Checking like status for user ID: {user_id} on short ID: {short_id}.")
        like = self.db.query(short_likes_model.ShortLike)\
            .filter(short_likes_model.ShortLike.user_id == user_id, short_likes_model.ShortLike.short_id == short_id)\
            .first()
        return like is not None
