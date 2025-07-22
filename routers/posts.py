# hive_server/routers/posts.py

from fastapi import APIRouter, Depends, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Literal, Dict

import logging

logger = logging.getLogger("tea_n_hive_logger.posts_router")

from ..controllers import posts as posts_controller
from ..schemas import posts as posts_schema
from ..utils.db import get_db
from ..utils.security import get_current_user, get_current_user_optional # <--- MODIFIED: Import get_current_user_optional
from ..models import user as user_model

router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)

# --- Post Endpoints ---
@router.post(
    "/",
    response_model=posts_schema.PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new post",
    description="Allows an authenticated user to create a new text, image, or video post. Accepts multipart/form-data for media files."
)
async def create_post(
    post_type: Literal["TEXT", "IMAGE", "VIDEO"] = Form(..., description="Type of the post (e.g., TEXT, IMAGE, VIDEO)."),
    text_content: Optional[str] = Form(None, max_length=1000, description="Main text content of the post."),
    media_file: Optional[UploadFile] = File(None, description="Optional image or video file to upload."),

    current_user: user_model.User = Depends(get_current_user), # This still requires authentication
    db: Session = Depends(get_db)
):
    """
    API endpoint to create a new post.
    Accepts form-data for text content and an optional file.
    """
    if isinstance(media_file, str) and not media_file:
        media_file = None
        logger.debug("Router: Detected empty string for media_file, treating as None.")
    elif media_file and not media_file.filename:
        media_file = None
        logger.debug("Router: Detected UploadFile with empty filename, treating as None.")

    post_create_data = posts_schema.PostCreate(
        post_type=post_type,
        text_content=text_content
    )

    return await posts_controller.create_post_controller(
        post_data=post_create_data,
        media_file=media_file,
        current_user=current_user,
        db=db
    )

@router.get(
    "/",
    response_model=List[posts_schema.PostResponse],
    summary="Get a list of posts",
    description="Retrieves a paginated list of all posts, including likes count and current user's like status if authenticated."
)
async def get_posts(
    skip: int = Query(0, ge=0, description="Number of items to skip (for pagination)."),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of items to return (for pagination)."),
    current_user: Optional[user_model.User] = Depends(get_current_user_optional), # <--- MODIFIED: Use optional auth
    db: Session = Depends(get_db)
):
    """
    API endpoint to retrieve multiple posts.
    """
    return posts_controller.get_posts_controller(
        skip=skip,
        limit=limit,
        current_user=current_user, # <--- MODIFIED: Pass current_user
        db=db
    )

@router.get(
    "/{post_id}",
    response_model=posts_schema.PostResponse,
    summary="Get a single post by ID",
    description="Retrieves the details of a specific post, including likes count and current user's like status if authenticated."
)
async def get_post(
    post_id: int,
    current_user: Optional[user_model.User] = Depends(get_current_user_optional), # <--- MODIFIED: Use optional auth
    db: Session = Depends(get_db)
):
    """
    API endpoint to retrieve a single post.
    """
    return posts_controller.get_post_controller(
        post_id=post_id,
        current_user=current_user, # <--- MODIFIED: Pass current_user
        db=db
    )

@router.put(
    "/{post_id}",
    response_model=posts_schema.PostResponse,
    summary="Update a post (full replacement)",
    description="Fully updates an existing post by ID. Requires authentication and ownership. This endpoint expects an application/json body."
)
async def update_post_put(
    post_id: int,
    post_data: posts_schema.PostUpdate,
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API endpoint to fully update a post.
    """
    return await posts_controller.update_post_controller(
        post_id=post_id,
        post_data=post_data,
        media_file=None,
        current_user=current_user,
        db=db
    )

@router.patch(
    "/{post_id}",
    response_model=posts_schema.PostResponse,
    summary="Partially update a post",
    description="Partially updates an existing post by ID. Requires authentication and ownership. Accepts multipart/form-data if a file is uploaded, or application/json for text-only updates."
)
async def update_post_patch(
    post_id: int,
    post_type: Optional[Literal["TEXT", "IMAGE", "VIDEO"]] = Form(None, description="Optional new type of the post."),
    text_content: Optional[str] = Form(None, max_length=1000, description="Optional new text content of the post."),
    media_file: Optional[UploadFile] = File(None, description="Optional new image or video file to upload."),

    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API endpoint to partially update a post.
    Accepts form-data for text content and an optional file.
    """
    if isinstance(media_file, str) and not media_file:
        media_file = None
        logger.debug("Router: Detected empty string for media_file, treating as None during PATCH.")
    elif media_file and not media_file.filename:
        media_file = None
        logger.debug("Router: Detected UploadFile with empty filename, treating as None during PATCH.")

    update_data = {}
    if post_type is not None:
        update_data["post_type"] = post_type
    if text_content is not None:
        update_data["text_content"] = text_content
    
    post_update_data = posts_schema.PostUpdate(**update_data)

    return await posts_controller.update_post_controller(
        post_id=post_id,
        post_data=post_update_data,
        media_file=media_file,
        current_user=current_user,
        db=db
    )


@router.delete(
    "/{post_id}",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Delete a post",
    description="Deletes a post by ID. Requires authentication and ownership."
)
async def delete_post(
    post_id: int,
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API endpoint to delete a post.
    Directly calls the controller function.
    """
    return posts_controller.delete_post_controller(
        post_id=post_id,
        current_user=current_user,
        db=db
    )
