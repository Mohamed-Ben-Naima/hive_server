# hive_server/routers/post_likes.py

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict # <--- ADDED: Import Dict

import logging

logger = logging.getLogger("tea_n_hive_logger.post_likes_router")

from ..controllers import post_likes as post_likes_controller
from ..schemas import post_likes as post_likes_schema
from ..models import user as user_model
from ..utils.db import get_db
from ..utils.security import get_current_user

router = APIRouter(
    prefix="/posts",
    tags=["Post Likes"]
)

# --- Post Likes Endpoints ---

@router.post(
    "/{post_id}/likes",
    response_model=post_likes_schema.PostLikeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Like a post",
    description="Allows an authenticated user to like a specific post. A user can only like a post once."
)
async def like_post(
    post_id: int,
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API endpoint to like a post.
    """
    return post_likes_controller.like_post_controller(
        post_id=post_id,
        current_user=current_user,
        db=db
    )

@router.delete(
    "/{post_id}/likes",
    response_model=Dict[str, str], # <--- MODIFIED: Change response_model to Dict[str, str]
    status_code=status.HTTP_200_OK, # <--- MODIFIED: Change status_code to 200 OK
    summary="Unlike a post",
    description="Allows an authenticated user to unlike a post they previously liked."
)
async def unlike_post(
    post_id: int,
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API endpoint to unlike a post.
    """
    return post_likes_controller.unlike_post_controller(
        post_id=post_id,
        current_user=current_user,
        db=db
    )

@router.get(
    "/{post_id}/likes",
    response_model=List[post_likes_schema.PostLikeResponse],
    summary="Get likes for a post",
    description="Retrieves a paginated list of users who liked a specific post."
)
async def get_likes_for_post(
    post_id: int,
    skip: int = Query(0, ge=0, description="Number of items to skip (for pagination)."),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of items to return (for pagination)."),
    db: Session = Depends(get_db)
):
    """
    API endpoint to retrieve likes for a specific post.
    """
    return post_likes_controller.get_likes_for_post_controller(
        post_id=post_id,
        skip=skip,
        limit=limit,
        db=db
    )

@router.get(
    "/users/{user_id}/likes",
    response_model=List[post_likes_schema.PostLikeResponse],
    summary="Get posts liked by a user",
    description="Retrieves a paginated list of posts liked by a specific user."
)
async def get_posts_liked_by_user(
    user_id: int,
    skip: int = Query(0, ge=0, description="Number of items to skip (for pagination)."),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of items to return (for pagination)."),
    db: Session = Depends(get_db)
):
    """
    API endpoint to retrieve posts liked by a specific user.
    """
    return post_likes_controller.get_posts_liked_by_user_controller(
        user_id=user_id,
        skip=skip,
        limit=limit,
        db=db
    )
