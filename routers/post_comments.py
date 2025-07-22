# hive_server/routers/post_comments.py

from fastapi import APIRouter, Depends, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict

import logging

logger = logging.getLogger("tea_n_hive_logger.post_comments_router")

from ..controllers import post_comments as post_comments_controller
from ..schemas import post_comments as post_comments_schema
from ..models import user as user_model
from ..utils.db import get_db
from ..utils.security import get_current_user

router = APIRouter(
    tags=["Post Comments"]
)

# --- Post Comments Endpoints ---

@router.post(
    "/posts/{post_id}/comments",
    response_model=post_comments_schema.PostCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new comment on a post",
    description="Allows an authenticated user to add a comment to a specific post."
)
async def create_comment(
    post_id: int,
    comment_data: post_comments_schema.PostCommentCreate = Body(..., description="Comment details"),
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API endpoint to create a new comment.
    """
    # Override post_id in comment_data with the one from the path for consistency and security
    comment_data.post_id = post_id 
    return post_comments_controller.create_comment_controller(
        post_id=post_id,
        comment_data=comment_data,
        current_user=current_user,
        db=db
    )

@router.get(
    "/posts/{post_id}/comments",
    response_model=List[post_comments_schema.PostCommentResponse],
    summary="Get all comments for a specific post",
    description="Retrieves a paginated list of comments associated with a given post."
)
async def get_comments_for_post(
    post_id: int,
    skip: int = Query(0, ge=0, description="Number of items to skip (for pagination)."),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of items to return (for pagination)."),
    db: Session = Depends(get_db)
):
    """
    API endpoint to retrieve comments for a specific post.
    """
    return post_comments_controller.get_comments_for_post_controller(
        post_id=post_id,
        skip=skip,
        limit=limit,
        db=db
    )

@router.get(
    "/comments/{comment_id}",
    response_model=post_comments_schema.PostCommentResponse,
    summary="Get a single comment by ID",
    description="Retrieves the details of a specific comment."
)
async def get_comment(
    comment_id: int,
    db: Session = Depends(get_db)
):
    """
    API endpoint to retrieve a single comment.
    """
    return post_comments_controller.get_comment_controller(
        comment_id=comment_id,
        db=db
    )

@router.patch(
    "/comments/{comment_id}",
    response_model=post_comments_schema.PostCommentResponse,
    summary="Partially update a comment",
    description="Allows the owner of a comment to update its text content."
)
async def update_comment(
    comment_id: int,
    comment_data: post_comments_schema.PostCommentUpdate = Body(..., description="Updated comment details"),
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API endpoint to update a comment.
    """
    return post_comments_controller.update_comment_controller(
        comment_id=comment_id,
        comment_data=comment_data, # <--- MODIFIED: Pass the entire comment_data object
        current_user=current_user,
        db=db
    )

@router.delete(
    "/comments/{comment_id}",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Delete a comment",
    description="Allows the owner of a comment to delete it."
)
async def delete_comment(
    comment_id: int,
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API endpoint to delete a comment.
    """
    return post_comments_controller.delete_comment_controller(
        comment_id=comment_id,
        current_user=current_user,
        db=db
    )
