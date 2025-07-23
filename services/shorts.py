# hive_server/services/shorts.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, select, literal_column
from fastapi import HTTPException, status, UploadFile
import logging
from typing import List, Optional

from ..utils import file_manager # For handling video file uploads

logger = logging.getLogger("tea_n_hive_logger.shorts_service")

from ..models import shorts as shorts_model
from ..models import user as user_model
from ..models import short_likes as short_likes_model # For likes count
from ..models import short_comments as short_comments_model # For comments count
from ..schemas import shorts as shorts_schema

class ShortsService:
    def __init__(self, db: Session):
        self.db = db

    async def create_short(self, user_id: int, short_data: shorts_schema.ShortCreate, video_file: UploadFile) -> shorts_model.Short:
        """
        Creates a new short video post for a given user, handling video file upload.
        Ensures the user exists and returns the newly created short with its author's profile eager-loaded.
        """
        logger.info(f"Attempting to create a new short for user ID: {user_id}.")
        
        user_exists = self.db.query(user_model.User).filter(user_model.User.user_id == user_id).first()
        if not user_exists:
            logger.warning(f"Short creation failed: User ID {user_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        video_filename_to_save = None
        
        # Validate video file presence
        if not video_file:
            logger.warning("Short creation failed: No video file provided.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A video file is required for creating a short."
            )
        
        # Save the video file
        video_filename_to_save = await file_manager.save_upload_file(video_file)

        try:
            db_short = shorts_model.Short(
                user_id=user_id,
                video_url=video_filename_to_save, # Store the filename/path
                description=short_data.description
            )
            self.db.add(db_short)
            self.db.commit()
            self.db.refresh(db_short)

            # Re-fetch the short with all necessary relationships eager-loaded for Pydantic.
            # Pass current_user_id=None because this is a creation, not a retrieval for a specific user.
            final_db_short = self.get_short_by_id(db_short.short_id, current_user_id=None)
            if not final_db_short:
                logger.error(f"Failed to retrieve newly created short ID: {db_short.short_id} after creation.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve newly created short for response."
                )

            logger.info(f"Successfully created short ID: {final_db_short.short_id} for user ID: {user_id}.")
            return final_db_short
        except HTTPException:
            # If an HTTPException was raised (e.g., user not found), re-raise it
            if video_filename_to_save:
                file_manager.delete_file(video_filename_to_save) # Clean up file if DB operation fails
                logger.info(f"Cleaned up orphaned video file: {video_filename_to_save}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Failed to create short for user ID: {user_id}. Rolling back transaction.")
            if video_filename_to_save:
                file_manager.delete_file(video_filename_to_save) # Clean up file if DB operation fails
                logger.info(f"Cleaned up orphaned video file: {video_filename_to_save}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create short due to a server error: {e}"
            )

    def get_short_by_id(self, short_id: int, current_user_id: Optional[int] = None) -> Optional[shorts_model.Short]:
        """
        Retrieves a single short by its ID, with its author's user and profile eager-loaded,
        and includes likes count, current user's like status, and comments count.
        """
        logger.debug(f"Attempting to retrieve short by ID: {short_id}.")

        # Subquery to count likes for the short
        likes_count_subquery = select(func.count(short_likes_model.ShortLike.like_id))\
            .where(short_likes_model.ShortLike.short_id == shorts_model.Short.short_id)\
            .scalar_subquery()

        # Subquery to check if current user liked the short
        is_liked_subquery = select(
            func.count(short_likes_model.ShortLike.like_id)
        ).where(
            short_likes_model.ShortLike.short_id == shorts_model.Short.short_id,
            short_likes_model.ShortLike.user_id == current_user_id # Filter by current user ID
        ).scalar_subquery()

        # Subquery to count comments for the short
        comments_count_subquery = select(func.count(short_comments_model.ShortComment.comment_id))\
            .where(short_comments_model.ShortComment.short_id == shorts_model.Short.short_id)\
            .scalar_subquery()

        # Build the main query for the short
        stmt = select(
            shorts_model.Short,
            likes_count_subquery.label("likes_count"),
            is_liked_subquery.label("is_liked_by_current_user"),
            comments_count_subquery.label("comments_count")
        ).options(
            joinedload(shorts_model.Short.user).joinedload(user_model.User.profile)
        ).filter(shorts_model.Short.short_id == short_id)

        # Execute the query
        result = self.db.execute(stmt).first()

        if not result:
            logger.warning(f"Short ID: {short_id} not found.")
            return None
        
        # Unpack the result: Short object and the three scalar values
        short_orm_obj, likes_count, is_liked_by_current_user_int, comments_count = result

        # Manually attach the calculated values to the ORM object for Pydantic serialization
        short_orm_obj.likes_count = likes_count
        short_orm_obj.is_liked_by_current_user = bool(is_liked_by_current_user_int)
        short_orm_obj.comments_count = comments_count

        logger.debug(f"Successfully retrieved short ID: {short_id} with likes count: {likes_count}, is_liked: {bool(is_liked_by_current_user_int)}, comments count: {comments_count}.")
        return short_orm_obj

    def get_shorts(self, skip: int = 0, limit: int = 10, current_user_id: Optional[int] = None) -> List[shorts_model.Short]:
        """
        Retrieves a paginated list of shorts, with each short's author and profile eager-loaded,
        and includes likes count, current user's like status, and comments count.
        """
        logger.debug(f"Attempting to retrieve shorts (skip: {skip}, limit: {limit}).")

        # Define aliases for tables to make joins clearer
        Short = shorts_model.Short
        User = user_model.User
        ShortLike = short_likes_model.ShortLike
        ShortComment = short_comments_model.ShortComment

        # CTE for likes count
        likes_count_cte = select(
            ShortLike.short_id,
            func.count(ShortLike.like_id).label("likes_count")
        ).group_by(ShortLike.short_id).cte("short_likes_count_cte")

        # CTE for current user's like status
        is_liked_cte = select(
            ShortLike.short_id
        ).where(
            ShortLike.user_id == current_user_id
        ).cte("short_is_liked_cte")

        # CTE for comments count
        comments_count_cte = select(
            ShortComment.short_id,
            func.count(ShortComment.comment_id).label("comments_count")
        ).group_by(ShortComment.short_id).cte("short_comments_count_cte")

        # Build the main query
        stmt = select(
            Short,
            func.coalesce(likes_count_cte.c.likes_count, 0).label("likes_count"),
            (is_liked_cte.c.short_id.is_not(None)).label("is_liked_by_current_user"),
            func.coalesce(comments_count_cte.c.comments_count, 0).label("comments_count")
        ).options(
            joinedload(Short.user).joinedload(User.profile)
        ).outerjoin(
            likes_count_cte, Short.short_id == likes_count_cte.c.short_id
        ).outerjoin(
            is_liked_cte, Short.short_id == is_liked_cte.c.short_id
        ).outerjoin(
            comments_count_cte, Short.short_id == comments_count_cte.c.short_id
        ).order_by(
            Short.created_at.desc()
        ).offset(skip).limit(limit)

        # Execute the query
        results = self.db.execute(stmt).all()

        shorts_with_data = []
        for row in results:
            # Unpack the result: Short object, likes_count, is_liked_by_current_user, comments_count
            short_orm_obj, likes_count, is_liked_by_current_user_bool, comments_count = row
            
            # Manually attach the calculated values to the ORM object
            short_orm_obj.likes_count = likes_count
            short_orm_obj.is_liked_by_current_user = is_liked_by_current_user_bool
            short_orm_obj.comments_count = comments_count
            shorts_with_data.append(short_orm_obj)

        logger.debug(f"Successfully retrieved {len(shorts_with_data)} shorts with likes and comments data.")
        return shorts_with_data

    async def update_short(self, short_id: int, user_id: int, short_data: shorts_schema.ShortUpdate, video_file: Optional[UploadFile]) -> shorts_model.Short:
        """
        Updates an existing short video post, handling optional video file updates.
        Ensures the authenticated user is the owner.
        """
        logger.info(f"Attempting to update short ID: {short_id} by user ID: {user_id}.")
        db_short = self.db.query(shorts_model.Short)\
            .options(joinedload(shorts_model.Short.user).joinedload(user_model.User.profile))\
            .filter(shorts_model.Short.short_id == short_id)\
            .first()

        if not db_short:
            logger.warning(f"Short update failed: Short ID {short_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short not found."
            )
        
        if db_short.user_id != user_id:
            logger.warning(f"Short update failed: User ID {user_id} is not the owner of short ID {short_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this short."
            )

        old_video_filename = db_short.video_url
        new_video_filename = None

        if short_data.description is not None:
            db_short.description = short_data.description

        if video_file:
            new_video_filename = await file_manager.save_upload_file(video_file)
            if old_video_filename:
                file_manager.delete_file(old_video_filename) # Delete old video file
            db_short.video_url = new_video_filename
            logger.info(f"Updated video file for short ID {short_id}. Old: {old_video_filename}, New: {new_video_filename}.")
        
        try:
            self.db.add(db_short)
            self.db.commit()
            self.db.refresh(db_short)
            
            # Re-fetch the short with all necessary relationships eager-loaded for Pydantic response.
            # Pass current_user_id for correct likes count and status.
            final_db_short = self.get_short_by_id(db_short.short_id, current_user_id=user_id)
            if not final_db_short:
                logger.error(f"Failed to retrieve updated short ID: {db_short.short_id} after update.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve updated short for response."
                )

            logger.info(f"Successfully updated short ID: {short_id}.")
            return final_db_short
        except HTTPException:
            # If an HTTPException was raised, re-raise it
            if video_file and new_video_filename:
                file_manager.delete_file(new_video_filename) # Clean up new file if DB operation fails
                logger.info(f"Cleaned up orphaned new video file: {new_video_filename}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.exception(f"An unexpected error occurred while updating short ID: {short_id} for user ID: {user_id}.")
            if video_file and new_video_filename:
                file_manager.delete_file(new_video_filename) # Clean up new file if DB operation fails
                logger.info(f"Cleaned up orphaned new video file: {new_video_filename}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update short due to a server error: {e}"
            )

    async def delete_short(self, short_id: int, user_id: int) -> None:
        """
        Deletes a short. Ensures the authenticated user is the owner and deletes associated video file.
        """
        logger.info(f"Attempting to delete short ID: {short_id} by user ID: {user_id}.")
        db_short = self.db.query(shorts_model.Short).filter(shorts_model.Short.short_id == short_id).first()

        if not db_short:
            logger.warning(f"Short deletion failed: Short ID {short_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short not found."
            )
        
        if db_short.user_id != user_id:
            logger.warning(f"Short deletion failed: User ID {user_id} is not the owner of short ID {short_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this short."
            )

        try:
            if db_short.video_url:
                file_manager.delete_file(db_short.video_url) # Delete the actual video file
                logger.info(f"Deleted video file: {db_short.video_url} for short ID: {short_id}.")

            self.db.delete(db_short)
            self.db.commit()
            logger.info(f"Successfully deleted short ID: {short_id}.")
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Failed to delete short ID: {short_id}. Rolling back transaction.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete short due to a server error: {e}"
            )
