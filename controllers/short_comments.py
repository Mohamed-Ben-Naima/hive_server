# hive_server/controllers/short_comments.py

from fastapi import Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
import logging
from typing import List, Dict

logger = logging.getLogger("tea_n_hive_logger.short_comments_controller")

from ..utils.db import get_db # Dependency for DB session
from ..utils.security import get_current_user # Dependency for current user
from ..schemas import short_comments as short_comments_schema # ShortComment schemas for request/response
from ..models import user as user_model # User model for type hinting current_user
from ..services.short_comments import ShortCommentsService # ShortCommentsService for business logic

# --- Short Comments Controllers ---

def create_comment_controller(
    short_id: int, # From path parameter
    comment_data: short_comments_schema.ShortCommentCreate, # From request body
    current_user: user_model.User = Depends(get_current_user), # Authenticated user
    db: Session = Depends(get_db) # Database session
) -> short_comments_schema.ShortCommentResponse:
    """
    Controller to create a new comment on a short.
    Delegates to ShortCommentsService for business logic.
    """
    logger.info(f"Received request to create comment for short ID: {short_id} by user ID: {current_user.user_id}.")
    # Override short_id in comment_data with the one from the path for consistency and security
    comment_data.short_id = short_id 

    short_comments_service = ShortCommentsService(db)
    try:
        db_comment = short_comments_service.create_comment(
            user_id=current_user.user_id,
            short_id=short_id, # Use short_id from path
            text_content=comment_data.text_content
        )
        
        # Validate and serialize the SQLAlchemy ORM object into the Pydantic response schema.
        comment_response = short_comments_schema.ShortCommentResponse.model_validate(db_comment)
        
        logger.info(f"Comment ID: {db_comment.comment_id} created successfully for short ID: {short_id} by user ID: {current_user.user_id}.")
        return comment_response
    except HTTPException:
        raise # Re-raise HTTP exceptions (e.g., 404 Not Found)
    except Exception as e:
        logger.exception(f"An unexpected error occurred while creating comment for short ID: {short_id} by user ID: {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during comment creation: {e}"
        )

def get_comment_controller(
    comment_id: int,
    db: Session = Depends(get_db)
) -> short_comments_schema.ShortCommentResponse:
    """
    Controller to retrieve a single comment by ID.
    Delegates to ShortCommentsService for business logic.
    """
    logger.info(f"Received request to retrieve comment ID: {comment_id}.")
    short_comments_service = ShortCommentsService(db)
    db_comment = short_comments_service.get_comment_by_id(comment_id)
    
    if not db_comment:
        logger.warning(f"Comment retrieval failed: Comment ID {comment_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found."
        )
    
    comment_response = short_comments_schema.ShortCommentResponse.model_validate(db_comment)

    logger.info(f"Successfully retrieved comment ID: {comment_id}.")
    return comment_response

def get_comments_for_short_controller(
    short_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> List[short_comments_schema.ShortCommentResponse]:
    """
    Controller to retrieve a paginated list of comments for a specific short.
    Delegates to ShortCommentsService for business logic.
    """
    logger.info(f"Received request to retrieve comments for short ID: {short_id} (skip: {skip}, limit: {limit}).")
    short_comments_service = ShortCommentsService(db)
    db_comments = short_comments_service.get_comments_for_short(short_id=short_id, skip=skip, limit=limit)
    
    # Convert list of ORM objects to list of Pydantic response models
    response_comments = [short_comments_schema.ShortCommentResponse.model_validate(comment) for comment in db_comments]

    logger.info(f"Successfully retrieved {len(response_comments)} comments for short ID: {short_id}.")
    return response_comments

def update_comment_controller(
    comment_id: int,
    user_id: int, 
    new_text_content: str,
    db: Session = Depends(get_db) 
) -> short_comments_schema.ShortCommentResponse:
    """
    Updates the text content of an existing comment.
    Ensures the authenticated user is the owner of the comment.
    """
    logger.info(f"Attempting to update comment ID: {comment_id} by user ID: {user_id}.")
    short_comments_service = ShortCommentsService(db) # Initialize service here
    try:
        db_comment = short_comments_service.update_comment(
            comment_id=comment_id,
            user_id=user_id, # Pass user_id to service
            new_text_content=new_text_content # Pass new_text_content to service
        )
        
        comment_response = short_comments_schema.ShortCommentResponse.model_validate(db_comment)

        logger.info(f"Comment ID: {comment_id} updated successfully by user ID: {user_id}.")
        return comment_response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred while updating comment ID: {comment_id} for user ID: {user_id}.")
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
    Delegates to ShortCommentsService for business logic.
    Returns a success message upon completion.
    """
    logger.info(f"Received request to delete comment ID: {comment_id} by user ID: {current_user.user_id}.")
    short_comments_service = ShortCommentsService(db)
    try:
        # The service method takes user_id directly, not the current_user object
        short_comments_service.delete_comment(comment_id=comment_id, user_id=current_user.user_id)
        logger.info(f"Successfully deleted comment ID: {comment_id}.")
        return {"message": f"Successfully deleted comment ID {comment_id}."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"An unexpected error occurred while deleting comment ID: {comment_id} for user ID: {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during comment deletion: {e}"
        )
