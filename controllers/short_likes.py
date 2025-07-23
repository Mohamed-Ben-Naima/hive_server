# hive_server/controllers/short_likes.py

from fastapi import Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import logging
from typing import List, Dict

logger = logging.getLogger("tea_n_hive_logger.short_likes_controller")

from ..utils.db import get_db # Dependency for DB session
from ..utils.security import get_current_user # Dependency for current user
from ..schemas import short_likes as short_likes_schema # ShortLike schemas for request/response
from ..models import user as user_model # User model for type hinting current_user
from ..services.short_likes import ShortLikesService # ShortLikesService for business logic

# --- Short Likes Controllers ---

def like_short_controller(
    short_id: int, # From path parameter
    current_user: user_model.User = Depends(get_current_user), # Authenticated user
    db: Session = Depends(get_db) # Database session
) -> short_likes_schema.ShortLikeResponse:
    """
    Controller to like a short.
    Delegates to ShortLikesService for business logic.
    """
    logger.info(f"Received request to like short ID: {short_id} by user ID: {current_user.user_id}.")
    short_likes_service = ShortLikesService(db)
    try:
        db_like = short_likes_service.like_short(
            user_id=current_user.user_id,
            short_id=short_id
        )
        
        # Validate and serialize the SQLAlchemy ORM object into the Pydantic response schema.
        like_response = short_likes_schema.ShortLikeResponse.model_validate(db_like)
        
        logger.info(f"Like ID: {db_like.like_id} created successfully for short ID: {short_id} by user ID: {current_user.user_id}.")
        return like_response
    except HTTPException:
        raise # Re-raise HTTP exceptions (e.g., 404 Not Found, 409 Conflict)
    except Exception as e:
        logger.exception(f"An unexpected error occurred while liking short ID: {short_id} for user ID: {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during liking short: {e}"
        )

def unlike_short_controller(
    short_id: int, # From path parameter
    current_user: user_model.User = Depends(get_current_user), # Authenticated user
    db: Session = Depends(get_db) # Database session
) -> Dict[str, str]:
    """
    Controller to unlike a short.
    Delegates to ShortLikesService for business logic.
    Returns a success message upon completion.
    """
    logger.info(f"Received request to unlike short ID: {short_id} by user ID: {current_user.user_id}.")
    short_likes_service = ShortLikesService(db)
    try:
        short_likes_service.unlike_short(
            user_id=current_user.user_id,
            short_id=short_id
        )
        logger.info(f"Successfully unliked short ID: {short_id} by user ID: {current_user.user_id}.")
        return {"message": f"Successfully unliked short ID {short_id}."}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred while unliking short ID: {short_id} for user ID: {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during unliking short: {e}"
        )

def get_likes_for_short_controller(
    short_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> List[short_likes_schema.ShortLikeResponse]:
    """
    Controller to retrieve a paginated list of likes for a specific short.
    Delegates to ShortLikesService for business logic.
    """
    logger.info(f"Received request to retrieve likes for short ID: {short_id} (skip: {skip}, limit: {limit}).")
    short_likes_service = ShortLikesService(db)
    db_likes = short_likes_service.get_likes_for_short(short_id=short_id, skip=skip, limit=limit)
    
    # Convert list of ORM objects to list of Pydantic response models
    response_likes = [short_likes_schema.ShortLikeResponse.model_validate(like) for like in db_likes]

    logger.info(f"Successfully retrieved {len(response_likes)} likes for short ID: {short_id}.")
    return response_likes

def get_shorts_liked_by_user_controller(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> List[short_likes_schema.ShortLikeResponse]:
    """
    Controller to retrieve a paginated list of shorts liked by a specific user.
    Delegates to ShortLikesService for business logic.
    """
    logger.info(f"Received request to retrieve shorts liked by user ID: {user_id} (skip: {skip}, limit: {limit}).")
    short_likes_service = ShortLikesService(db)
    db_likes = short_likes_service.get_shorts_liked_by_user(user_id=user_id, skip=skip, limit=limit)
    
    # Convert list of ORM objects to list of Pydantic response models
    response_likes = [short_likes_schema.ShortLikeResponse.model_validate(like) for like in db_likes]

    logger.info(f"Successfully retrieved {len(response_likes)} liked shorts for user ID: {user_id}.")
    return response_likes
