# hive_server/services/short_comments.py

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
import logging
from typing import Optional, List

logger = logging.getLogger("tea_n_hive_logger.short_comments_service")

from ..models import short_comments as short_comments_model
from ..models import shorts as shorts_model # To check if short exists
from ..models import user as user_model # To check if user exists and eager load for response
from ..schemas import short_comments as short_comments_schema

class ShortCommentsService:
    def __init__(self, db: Session):
        self.db = db

    def create_comment(self, user_id: int, short_id: int, text_content: str) -> short_comments_model.ShortComment:
        """
        Creates a new comment for a specific short by a user.
        Raises HTTPException if the short or user does not exist.
        """
        logger.info(f"Attempting to create comment for short ID: {short_id} by user ID: {user_id}.")

        # 1. Verify Short Existence
        short_exists = self.db.query(shorts_model.Short).filter(shorts_model.Short.short_id == short_id).first()
        if not short_exists:
            logger.warning(f"Comment creation failed: Short ID {short_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short not found."
            )
        
        # 2. Verify User Existence (though current_user from dependency usually ensures this)
        user_exists = self.db.query(user_model.User).filter(user_model.User.user_id == user_id).first()
        if not user_exists:
            logger.warning(f"Comment creation failed: User ID {user_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        # 3. Create the Comment record
        db_comment = short_comments_model.ShortComment(
            user_id=user_id,
            short_id=short_id,
            text_content=text_content
        )
        try:
            self.db.add(db_comment)
            self.db.commit()
            self.db.refresh(db_comment) # Refresh to get comment_id and created_at

            # Eager load user and profile for the response schema
            final_db_comment = self.db.query(short_comments_model.ShortComment)\
                .options(joinedload(short_comments_model.ShortComment.user).joinedload(user_model.User.profile))\
                .filter(short_comments_model.ShortComment.comment_id == db_comment.comment_id)\
                .first()
            
            if not final_db_comment: # Should not happen if commit was successful
                logger.error(f"Failed to retrieve newly created comment ID: {db_comment.comment_id} after creation.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve comment for response."
                )

            logger.info(f"Successfully created comment ID: {final_db_comment.comment_id} for short ID: {short_id} by user ID: {user_id}.")
            return final_db_comment
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Failed to create comment for short ID: {short_id} by user ID: {user_id}. Rolling back transaction.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create comment due to a server error: {e}"
            )

    def get_comment_by_id(self, comment_id: int) -> Optional[short_comments_model.ShortComment]:
        """
        Retrieves a single comment by its ID, with its author's user and profile eager-loaded.
        """
        logger.debug(f"Attempting to retrieve comment by ID: {comment_id}.")
        comment = self.db.query(short_comments_model.ShortComment)\
            .options(joinedload(short_comments_model.ShortComment.user).joinedload(user_model.User.profile))\
            .filter(short_comments_model.ShortComment.comment_id == comment_id)\
            .first()
        
        if not comment:
            logger.warning(f"Comment ID: {comment_id} not found.")
            return None
        
        logger.debug(f"Successfully retrieved comment ID: {comment_id}.")
        return comment

    def get_comments_for_short(self, short_id: int, skip: int = 0, limit: int = 10) -> List[short_comments_model.ShortComment]:
        """
        Retrieves a paginated list of comments for a specific short, with commenter's user and profile eager-loaded.
        """
        logger.debug(f"Attempting to retrieve comments for short ID: {short_id} (skip: {skip}, limit: {limit}).")
        comments = self.db.query(short_comments_model.ShortComment)\
            .options(joinedload(short_comments_model.ShortComment.user).joinedload(user_model.User.profile))\
            .filter(short_comments_model.ShortComment.short_id == short_id)\
            .order_by(short_comments_model.ShortComment.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        
        logger.debug(f"Successfully retrieved {len(comments)} comments for short ID: {short_id}.")
        return comments

    def update_comment(self, comment_id: int, user_id: int, new_text_content: str) -> short_comments_model.ShortComment:
        """
        Updates the text content of an existing comment.
        Ensures the authenticated user is the owner of the comment.
        """
        logger.info(f"Attempting to update comment ID: {comment_id} by user ID: {user_id}.")
        db_comment = self.db.query(short_comments_model.ShortComment)\
            .filter(short_comments_model.ShortComment.comment_id == comment_id)\
            .first()

        if not db_comment:
            logger.warning(f"Comment update failed: Comment ID {comment_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found."
            )
        
        if db_comment.user_id != user_id:
            logger.warning(f"Comment update failed: User ID {user_id} is not the owner of comment ID {comment_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this comment."
            )

        db_comment.text_content = new_text_content
        
        try:
            self.db.add(db_comment) # Add the modified object to the session
            self.db.commit() # Commit changes to the database
            self.db.refresh(db_comment) # Refresh the object to reflect latest DB state

            # Re-fetch the comment with all necessary relationships eager-loaded for Pydantic response.
            final_db_comment = self.db.query(short_comments_model.ShortComment)\
                .options(joinedload(short_comments_model.ShortComment.user).joinedload(user_model.User.profile))\
                .filter(short_comments_model.ShortComment.comment_id == db_comment.comment_id)\
                .first()
            
            if not final_db_comment:
                logger.error(f"Failed to retrieve updated comment ID: {db_comment.comment_id} after update.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve updated comment for response."
                )

            logger.info(f"Successfully updated comment ID: {comment_id}.")
            return final_db_comment
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.exception(f"An unexpected error occurred while updating comment ID: {comment_id} for user ID: {user_id}.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update comment due to a server error: {e}"
            )

    def delete_comment(self, comment_id: int, user_id: int) -> None:
        """
        Deletes a comment. Ensures the authenticated user is the owner.
        """
        logger.info(f"Attempting to delete comment ID: {comment_id} by user ID: {user_id}.")
        db_comment = self.db.query(short_comments_model.ShortComment)\
            .filter(short_comments_model.ShortComment.comment_id == comment_id)\
            .first()

        if not db_comment:
            logger.warning(f"Comment deletion failed: Comment ID {comment_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found."
            )
        
        if db_comment.user_id != user_id:
            logger.warning(f"Comment deletion failed: User ID {user_id} is not the owner of comment ID {comment_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this comment."
            )

        try:
            self.db.delete(db_comment)
            self.db.commit()
            logger.info(f"Successfully deleted comment ID: {comment_id}.")
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Failed to delete comment ID: {comment_id}. Rolling back transaction.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete comment due to a server error: {e}"
            )
