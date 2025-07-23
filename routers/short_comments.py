# hive_server/routers/short_comments.py (Your provided code, which is now correct for the controller)

from fastapi import APIRouter, Depends, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict

import logging

logger = logging.getLogger("tea_n_hive_logger.short_comments_router")

from ..controllers import short_comments as short_comments_controller # Import the short_comments controller
from ..schemas import short_comments as short_comments_schema # Import short_comments schemas
from ..models import user as user_model # User model for type hinting current_user
from ..utils.db import get_db # Dependency for DB session
from ..utils.security import get_current_user # Dependency for current user

router = APIRouter(
    tags=["Short Comments"] # Used for Swagger UI grouping
)

# --- Short Comments Endpoints ---

@router.post(
    "/shorts/{short_id}/comments",
    response_model=short_comments_schema.ShortCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new comment on a short video",
    description="Allows an authenticated user to add a comment to a specific short video."
)
async def create_comment(
    short_id: int, # Path parameter for the short
    comment_data: short_comments_schema.ShortCommentCreate = Body(..., description="Comment details"), # Request body
    current_user: user_model.User = Depends(get_current_user), # Authenticated user
    db: Session = Depends(get_db)
):
    """
    API endpoint to create a new comment on a short.
    """
    # Override short_id in comment_data with the one from the path for consistency and security
    comment_data.short_id = short_id 
    return short_comments_controller.create_comment_controller(
        short_id=short_id, # Pass short_id from path
        comment_data=comment_data,
        current_user=current_user, # Pass the current_user dependency
        db=db
    )

@router.get(
    "/shorts/{short_id}/comments",
    response_model=List[short_comments_schema.ShortCommentResponse],
    summary="Get all comments for a specific short video",
    description="Retrieves a paginated list of comments associated with a given short video."
)
async def get_comments_for_short(
    short_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    API endpoint to retrieve comments for a specific short.
    """
    return short_comments_controller.get_comments_for_short_controller(
        short_id=short_id,
        skip=skip,
        limit=limit,
        db=db
    )

@router.get(
    "/shorts/comments/{comment_id}", # Direct access to a short comment by its ID
    response_model=short_comments_schema.ShortCommentResponse,
    summary="Get a single short comment by ID",
    description="Retrieves the details of a specific comment on a short video."
)
async def get_comment(
    comment_id: int,
    db: Session = Depends(get_db)
):
    """
    API endpoint to retrieve a single short comment.
    """
    return short_comments_controller.get_comment_controller(
        comment_id=comment_id,
        db=db
    )

@router.patch(
    "/shorts/comments/{comment_id}",
    response_model=short_comments_schema.ShortCommentResponse,
    summary="Partially update a short comment",
    description="Allows the owner of a short comment to update its text content."
)
async def update_comment(
    comment_id: int,
    comment_data: short_comments_schema.ShortCommentUpdate = Body(..., description="Updated comment details"),
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API endpoint to update a short comment.
    """
    return short_comments_controller.update_comment_controller(
        comment_id=comment_id,
        user_id=current_user.user_id, # MODIFIED: Pass user_id directly
        new_text_content=comment_data.text_content, # MODIFIED: Pass text_content directly
        db=db # MODIFIED: Pass db directly (as it's a dependency in controller)
    )

@router.delete(
    "/shorts/comments/{comment_id}",
    response_model=Dict[str, str], # Return a message on successful deletion
    status_code=status.HTTP_200_OK,
    summary="Delete a short comment",
    description="Allows the owner of a short comment to delete it."
)
async def delete_comment(
    comment_id: int,
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API endpoint to delete a short comment.
    """
    return short_comments_controller.delete_comment_controller(
        comment_id=comment_id,
        current_user=current_user, # Pass the current_user dependency
        db=db # Pass the db dependency
    )