# hive_server/routers/short_likes.py

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict

import logging

logger = logging.getLogger("tea_n_hive_logger.short_likes_router")

from ..controllers import short_likes as short_likes_controller # Import the short_likes controller
from ..schemas import short_likes as short_likes_schema # Import short_likes schemas
from ..models import user as user_model # User model for type hinting current_user
from ..utils.db import get_db # Dependency for DB session
from ..utils.security import get_current_user # Dependency for current user

router = APIRouter(
    tags=["Short Likes"] # Used for Swagger UI grouping
)

# --- Short Likes Endpoints ---

@router.post(
    "/shorts/{short_id}/likes",
    response_model=short_likes_schema.ShortLikeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Like a short video",
    description="Allows an authenticated user to like a specific short video."
)
async def like_short(
    short_id: int, # Path parameter for the short
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API endpoint to like a short.
    """
    return short_likes_controller.like_short_controller(
        # MODIFIED: Removed user_id as it's passed via current_user dependency in controller
        short_id=short_id,
        current_user=current_user, # Pass the current_user dependency
        db=db
    )

@router.delete(
    "/shorts/{short_id}/likes",
    response_model=Dict[str, str], # Return a message on successful unliking
    status_code=status.HTTP_200_OK,
    summary="Unlike a short video",
    description="Allows an authenticated user to remove their like from a specific short video."
)
async def unlike_short(
    short_id: int, # Path parameter for the short
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API endpoint to unlike a short.
    """
    return short_likes_controller.unlike_short_controller(
        # MODIFIED: Removed user_id as it's passed via current_user dependency in controller
        short_id=short_id,
        current_user=current_user, # Pass the current_user dependency
        db=db
    )

@router.get(
    "/shorts/{short_id}/likes",
    response_model=List[short_likes_schema.ShortLikeResponse],
    summary="Get all likes for a specific short",
    description="Retrieves a paginated list of likes associated with a given short video."
)
async def get_likes_for_short(
    short_id: int,
    skip: int = Query(0, ge=0, description="Number of items to skip (for pagination)."),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of items to return (for pagination)."),
    db: Session = Depends(get_db)
):
    """
    API endpoint to retrieve likes for a specific short.
    """
    return short_likes_controller.get_likes_for_short_controller(
        short_id=short_id,
        skip=skip,
        limit=limit,
        db=db
    )

@router.get(
    "/shorts/users/{user_id}/likes", # Note: This path is different from /shorts/{short_id}/likes
    response_model=List[short_likes_schema.ShortLikeResponse],
    summary="Get all shorts liked by a specific user",
    description="Retrieves a paginated list of short videos that a given user has liked."
)
async def get_shorts_liked_by_user(
    user_id: int,
    skip: int = Query(0, ge=0, description="Number of items to skip (for pagination)."),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of items to return (for pagination)."),
    db: Session = Depends(get_db)
):
    """
    API endpoint to retrieve shorts liked by a specific user.
    """
    return short_likes_controller.get_shorts_liked_by_user_controller(
        user_id=user_id,
        skip=skip,
        limit=limit,
        db=db
    )
