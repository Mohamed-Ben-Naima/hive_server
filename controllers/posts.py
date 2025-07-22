# hive_server/controllers/posts.py

from fastapi import Depends, HTTPException, status, Query, UploadFile
from sqlalchemy.orm import Session
import logging
from typing import List, Optional

logger = logging.getLogger("tea_n_hive_logger.posts_controller")

from ..utils.db import get_db
from ..utils.security import get_current_user
from ..schemas import posts as posts_schema
from ..schemas import user as user_schema
from ..services.posts import PostsService
from ..models import user as user_model

# --- Post Controllers ---
async def create_post_controller(
    post_data: posts_schema.PostCreate,
    media_file: Optional[UploadFile],
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> posts_schema.PostResponse:
    """
    Controller to create a new post, potentially with a file upload.
    """
    logger.info(f"Received request to create post by user ID: {current_user.user_id}.")
    posts_service = PostsService(db)
    try:
        db_post = await posts_service.create_post(
            user_id=current_user.user_id,
            post_data=post_data,
            media_file=media_file
        )
        
        # --- DEBUGGING IN CONTROLLER ---
        logger.debug(f"Controller DEBUG: db_post object type: {type(db_post)}")
        if db_post.user:
            logger.debug(f"Controller DEBUG: db_post.user object type: {type(db_post.user)}")
            logger.debug(f"Controller DEBUG: db_post.user.profile object: {db_post.user.profile}")
            if hasattr(db_post.user, 'profile') and db_post.user.profile:
                logger.debug(f"Controller DEBUG: db_post.user.profile.username: {db_post.user.profile.username}")
            else:
                logger.debug("Controller DEBUG: db_post.user.profile is not loaded or does not exist on ORM object.")
        else:
            logger.debug("Controller DEBUG: db_post.user is None.")
        # --- END DEBUGGING ---

        post_response = posts_schema.PostResponse.model_validate(db_post)
        
        logger.info(f"Post ID: {db_post.post_id} created successfully by user ID: {current_user.user_id}.")
        return post_response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred while creating post for user ID: {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during post creation: {e}"
        )

def get_post_controller(
    post_id: int,
    db: Session = Depends(get_db)
) -> posts_schema.PostResponse:
    """
    Controller to retrieve a single post by ID.
    """
    logger.info(f"Received request to retrieve post ID: {post_id}.")
    posts_service = PostsService(db)
    db_post = posts_service.get_post_by_id(post_id)
    
    if not db_post:
        logger.warning(f"Post retrieval failed: Post ID {post_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found."
        )
    
    post_response = posts_schema.PostResponse.model_validate(db_post)

    logger.info(f"Successfully retrieved post ID: {post_id}.")
    return post_response

def get_posts_controller(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> List[posts_schema.PostResponse]:
    """
    Controller to retrieve a list of posts with pagination.
    """
    logger.info(f"Received request to retrieve posts (skip: {skip}, limit: {limit}).")
    posts_service = PostsService(db)
    db_posts = posts_service.get_posts(skip=skip, limit=limit)
    
    response_posts = [posts_schema.PostResponse.model_validate(post) for post in db_posts]

    logger.info(f"Successfully retrieved {len(response_posts)} posts.")
    return response_posts

async def update_post_controller(
    post_id: int,
    post_data: posts_schema.PostUpdate,
    media_file: Optional[UploadFile],
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> posts_schema.PostResponse:
    """
    Controller to update an existing post, potentially with a file upload.
    """
    logger.info(f"Received request to update post ID: {post_id} by user ID: {current_user.user_id}.")
    posts_service = PostsService(db)
    try:
        db_post = await posts_service.update_post(
            post_id=post_id,
            user_id=current_user.user_id,
            post_data=post_data,
            media_file=media_file
        )
        
        # --- DEBUGGING IN CONTROLLER ---
        logger.debug(f"Controller DEBUG: db_post object type: {type(db_post)}")
        if db_post.user:
            logger.debug(f"Controller DEBUG: db_post.user object type: {type(db_post.user)}")
            logger.debug(f"Controller DEBUG: db_post.user.profile object: {db_post.user.profile}")
            if hasattr(db_post.user, 'profile') and db_post.user.profile:
                logger.debug(f"Controller DEBUG: db_post.user.profile.username: {db_post.user.profile.username}")
            else:
                logger.debug("Controller DEBUG: db_post.user.profile is not loaded or does not exist on ORM object.")
        else:
            logger.debug("Controller DEBUG: db_post.user is None.")
        # --- END DEBUGGING ---

        post_response = posts_schema.PostResponse.model_validate(db_post)

        logger.info(f"Post ID: {post_id} updated successfully by user ID: {current_user.user_id}.")
        return post_response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred while updating post ID: {post_id} for user ID: {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during post update: {e}"
        )

def delete_post_controller(
    post_id: int,
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Controller to delete a post.
    """
    logger.info(f"Received request to delete post ID: {post_id} by user ID: {current_user.user_id}.")
    posts_service = PostsService(db)
    try:
        posts_service.delete_post(post_id=post_id, user_id=current_user.user_id)
        logger.info(f"Post ID: {post_id} deleted successfully by user ID: {current_user.user_id}.")
        return {"message": f"Post ID {post_id} deleted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred while deleting post ID: {post_id} for user ID: {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during post deletion: {e}"
        )