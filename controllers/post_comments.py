# hive_server/controllers/post_comments.py

from fastapi import Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import logging
from typing import List, Dict

logger = logging.getLogger("tea_n_hive_logger.post_comments_controller")

from ..utils.db import get_db # Dependency for DB session
from ..utils.security import get_current_user # Dependency for current user
from ..schemas import post_comments as post_comments_schema # PostComment schemas for request/response
from ..models import user as user_model # User model for type hinting current_user
from ..services.post_comments import PostCommentsService # PostCommentsService for business logic

# --- Post Comments Controllers ---

def create_comment_controller(
    post_id: int, # From path parameter
    comment_data: post_comments_schema.PostCommentCreate, # From request body
    current_user: user_model.User = Depends(get_current_user), # Authenticated user
    db: Session = Depends(get_db) # Database session
) -> post_comments_schema.PostCommentResponse:
    """
    Controller to create a new comment on a post.
    Delegates to PostCommentsService for business logic.
    """
    logger.info(f"Received request to create comment for post ID: {post_id} by user ID: {current_user.user_id}.")
    post_comments_service = PostCommentsService(db)
    try:
        db_comment = post_comments_service.create_comment(
            user_id=current_user.user_id,
            post_id=post_id, # Use post_id from path, not from comment_data (which also has it)
            text_content=comment_data.text_content
        )
        
        # Validate and serialize the SQLAlchemy ORM object into the Pydantic response schema.
        comment_response = post_comments_schema.PostCommentResponse.model_validate(db_comment)
        
        logger.info(f"Comment ID: {db_comment.comment_id} created successfully for post ID: {post_id} by user ID: {current_user.user_id}.")
        return comment_response
    except HTTPException:
        raise # Re-raise HTTP exceptions (e.g., 404 Not Found)
    except Exception as e:
        logger.exception(f"An unexpected error occurred while creating comment for post ID: {post_id} by user ID: {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during comment creation: {e}"
        )

def get_comment_controller(
    comment_id: int,
    db: Session = Depends(get_db)
) -> post_comments_schema.PostCommentResponse:
    """
    Controller to retrieve a single comment by ID.
    Delegates to PostCommentsService for business logic.
    """
    logger.info(f"Received request to retrieve comment ID: {comment_id}.")
    post_comments_service = PostCommentsService(db)
    db_comment = post_comments_service.get_comment_by_id(comment_id)
    
    if not db_comment:
        logger.warning(f"Comment retrieval failed: Comment ID {comment_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found."
        )
    
    comment_response = post_comments_schema.PostCommentResponse.model_validate(db_comment)

    logger.info(f"Successfully retrieved comment ID: {comment_id}.")
    return comment_response

def get_comments_for_post_controller(
    post_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> List[post_comments_schema.PostCommentResponse]:
    """
    Controller to retrieve a paginated list of comments for a specific post.
    Delegates to PostCommentsService for business logic.
    """
    logger.info(f"Received request to retrieve comments for post ID: {post_id} (skip: {skip}, limit: {limit}).")
    post_comments_service = PostCommentsService(db)
    db_comments = post_comments_service.get_comments_for_post(post_id=post_id, skip=skip, limit=limit)
    
    # Convert list of ORM objects to list of Pydantic response models
    response_comments = [post_comments_schema.PostCommentResponse.model_validate(comment) for comment in db_comments]

    logger.info(f"Successfully retrieved {len(response_comments)} comments for post ID: {post_id}.")
    return response_comments

def update_comment_controller(
    comment_id: int,
    comment_data: post_comments_schema.PostCommentUpdate, # From request body
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> post_comments_schema.PostCommentResponse:
    """
    Controller to update an existing comment.
    Delegates to PostCommentsService for business logic.
    """
    logger.info(f"Received request to update comment ID: {comment_id} by user ID: {current_user.user_id}.")
    post_comments_service = PostCommentsService(db)
    try:
        db_comment = post_comments_service.update_comment(
            comment_id=comment_id,
            user_id=current_user.user_id,
            new_text_content=comment_data.text_content
        )
        
        comment_response = post_comments_schema.PostCommentResponse.model_validate(db_comment)

        logger.info(f"Comment ID: {comment_id} updated successfully by user ID: {current_user.user_id}.")
        return comment_response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred while updating comment ID: {comment_id} for user ID: {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during comment update: {e}"
        )

def delete_comment_controller(
    comment_id: int,
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Controller to delete a comment.
    Delegates to PostCommentsService for business logic.
    Returns a success message upon completion.
    """
    logger.info(f"Received request to delete comment ID: {comment_id} by user ID: {current_user.user_id}.")
    post_comments_service = PostCommentsService(db)
    try:
        post_comments_service.delete_comment(comment_id=comment_id, user_id=current_user.user_id)
        logger.info(f"Comment ID: {comment_id} deleted successfully by user ID: {current_user.user_id}.")
        return {"message": f"Successfully deleted comment ID {comment_id}."}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred while deleting comment ID: {comment_id} for user ID: {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during comment deletion: {e}"
        )
