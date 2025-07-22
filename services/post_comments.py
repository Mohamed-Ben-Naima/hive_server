# hive_server/services/post_comments.py

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
import logging
from typing import Optional, List

logger = logging.getLogger("tea_n_hive_logger.post_comments_service")

from ..models import post_comments as post_comments_model
from ..models import posts as posts_model # To check if post exists
from ..models import user as user_model # To check if user exists and eager load for response
from ..schemas import post_comments as post_comments_schema

class PostCommentsService:
    def __init__(self, db: Session):
        self.db = db

    def create_comment(self, user_id: int, post_id: int, text_content: str) -> post_comments_model.PostComment:
        """
        Creates a new comment for a specific post by a user.
        Raises HTTPException if the post or user does not exist.
        """
        logger.info(f"Attempting to create comment for post ID: {post_id} by user ID: {user_id}.")

        # 1. Verify Post Existence
        post_exists = self.db.query(posts_model.Post).filter(posts_model.Post.post_id == post_id).first()
        if not post_exists:
            logger.warning(f"Comment creation failed: Post ID {post_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found."
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
        db_comment = post_comments_model.PostComment(
            user_id=user_id,
            post_id=post_id,
            text_content=text_content
        )
        try:
            self.db.add(db_comment)
            self.db.commit()
            self.db.refresh(db_comment) # Refresh to get comment_id and created_at

            # Eager load user and profile for the response schema
            final_db_comment = self.db.query(post_comments_model.PostComment)\
                .options(joinedload(post_comments_model.PostComment.user).joinedload(user_model.User.profile))\
                .filter(post_comments_model.PostComment.comment_id == db_comment.comment_id)\
                .first()
            
            if not final_db_comment: # Should not happen if commit was successful
                logger.error(f"Failed to retrieve newly created comment ID: {db_comment.comment_id} after creation.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve comment for response."
                )

            logger.info(f"Successfully created comment ID: {final_db_comment.comment_id} for post ID: {post_id} by user ID: {user_id}.")
            return final_db_comment
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Failed to create comment for post ID: {post_id} by user ID: {user_id}. Rolling back transaction.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create comment due to a server error: {e}"
            )

    def get_comment_by_id(self, comment_id: int) -> Optional[post_comments_model.PostComment]:
        """
        Retrieves a single comment by its ID, with its author's user and profile eager-loaded.
        """
        logger.debug(f"Attempting to retrieve comment by ID: {comment_id}.")
        comment = self.db.query(post_comments_model.PostComment)\
            .options(joinedload(post_comments_model.PostComment.user).joinedload(user_model.User.profile))\
            .filter(post_comments_model.PostComment.comment_id == comment_id)\
            .first()
        
        if not comment:
            logger.warning(f"Comment ID: {comment_id} not found.")
            return None
        
        logger.debug(f"Successfully retrieved comment ID: {comment_id}.")
        return comment

    def get_comments_for_post(self, post_id: int, skip: int = 0, limit: int = 10) -> List[post_comments_model.PostComment]:
        """
        Retrieves a paginated list of comments for a specific post, with commenter's user and profile eager-loaded.
        """
        logger.debug(f"Attempting to retrieve comments for post ID: {post_id} (skip: {skip}, limit: {limit}).")
        comments = self.db.query(post_comments_model.PostComment)\
            .options(joinedload(post_comments_model.PostComment.user).joinedload(user_model.User.profile))\
            .filter(post_comments_model.PostComment.post_id == post_id)\
            .order_by(post_comments_model.PostComment.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        
        logger.debug(f"Successfully retrieved {len(comments)} comments for post ID: {post_id}.")
        return comments

    def update_comment(self, comment_id: int, user_id: int, new_text_content: str) -> post_comments_model.PostComment:
        """
        Updates the text content of an existing comment.
        Ensures the authenticated user is the owner of the comment.
        """
        logger.info(f"Attempting to update comment ID: {comment_id} by user ID: {user_id}.")
        db_comment = self.db.query(post_comments_model.PostComment)\
            .filter(post_comments_model.PostComment.comment_id == comment_id)\
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
            final_db_comment = self.db.query(post_comments_model.PostComment)\
                .options(joinedload(post_comments_model.PostComment.user).joinedload(user_model.User.profile))\
                .filter(post_comments_model.PostComment.comment_id == db_comment.comment_id)\
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
        db_comment = self.db.query(post_comments_model.PostComment)\
            .filter(post_comments_model.PostComment.comment_id == comment_id)\
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
