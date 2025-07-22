# hive_server/controllers/post_likes.py

from fastapi import Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import logging
from typing import List, Dict # <--- ADDED: Import Dict for returning a message

logger = logging.getLogger("tea_n_hive_logger.post_likes_controller")

from ..utils.db import get_db
from ..utils.security import get_current_user
from ..schemas import post_likes as post_likes_schema
from ..models import user as user_model
from ..services.post_likes import PostLikesService

# --- Post Likes Controllers ---
def like_post_controller(
    post_id: int,
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> post_likes_schema.PostLikeResponse:
    """
    Controller to record a like for a post.
    Delegates to PostLikesService for business logic.
    """
    logger.info(f"Received request to like post ID: {post_id} by user ID: {current_user.user_id}.")
    post_likes_service = PostLikesService(db)
    try:
        db_like = post_likes_service.like_post(user_id=current_user.user_id, post_id=post_id)
        
        like_response = post_likes_schema.PostLikeResponse.model_validate(db_like)
        
        logger.info(f"Post ID: {post_id} liked successfully by user ID: {current_user.user_id}. Like ID: {db_like.like_id}.")
        return like_response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred while liking post ID: {post_id} for user ID: {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during liking post: {e}"
        )

def unlike_post_controller(
    post_id: int,
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]: # <--- MODIFIED: Change return type to Dict[str, str]
    """
    Controller to remove a like from a post.
    Delegates to PostLikesService for business logic.
    Returns a success message upon completion.
    """
    logger.info(f"Received request to unlike post ID: {post_id} by user ID: {current_user.user_id}.")
    post_likes_service = PostLikesService(db)
    try:
        post_likes_service.unlike_post(user_id=current_user.user_id, post_id=post_id)
        logger.info(f"Post ID: {post_id} unliked successfully by user ID: {current_user.user_id}.")
        return {"message": f"Successfully unliked post ID {post_id}."} # <--- MODIFIED: Return a dictionary
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred while unliking post ID: {post_id} for user ID: {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during unliking post: {e}"
        )

def get_likes_for_post_controller(
    post_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> List[post_likes_schema.PostLikeResponse]:
    """
    Controller to retrieve a paginated list of likes for a specific post.
    """
    logger.info(f"Received request to retrieve likes for post ID: {post_id} (skip: {skip}, limit: {limit}).")
    post_likes_service = PostLikesService(db)
    db_likes = post_likes_service.get_likes_for_post(post_id=post_id, skip=skip, limit=limit)
    
    response_likes = [post_likes_schema.PostLikeResponse.model_validate(like) for like in db_likes]

    logger.info(f"Successfully retrieved {len(response_likes)} likes for post ID: {post_id}.")
    return response_likes

def get_posts_liked_by_user_controller(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> List[post_likes_schema.PostLikeResponse]:
    """
    Controller to retrieve a paginated list of posts liked by a specific user.
    """
    logger.info(f"Received request to retrieve posts liked by user ID: {user_id} (skip: {skip}, limit: {limit}).")
    post_likes_service = PostLikesService(db)
    db_likes = post_likes_service.get_posts_liked_by_user(user_id=user_id, skip=skip, limit=limit)

    response_likes = [post_likes_schema.PostLikeResponse.model_validate(like) for like in db_likes]

    logger.info(f"Successfully retrieved {len(response_likes)} liked posts for user ID: {user_id}.")
    return response_likes
