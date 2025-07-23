# hive_server/routers/shorts.py

from fastapi import APIRouter, Depends, status, Query, UploadFile, File, Form, HTTPException # <--- ADDED: UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict

import logging

logger = logging.getLogger("tea_n_hive_logger.shorts_router")

from ..controllers import shorts as shorts_controller # Import the shorts controller
from ..schemas import shorts as shorts_schema # Import shorts schemas
from ..models import user as user_model # User model for type hinting current_user
from ..utils.db import get_db # Dependency for DB session
from ..utils.security import get_current_user, get_current_user_optional # Dependencies for current user

router = APIRouter(
    prefix="/shorts", # All endpoints in this router will start with /shorts
    tags=["Shorts"] # Used for Swagger UI grouping
)

# --- Shorts Endpoints ---

@router.post(
    "/",
    response_model=shorts_schema.ShortResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new short video post",
    description="Allows an authenticated user to upload a short video with an optional description."
)
async def create_short(
    description: Optional[str] = Form(None, max_length=500, description="Optional text description or caption for the short."),
    video_file: UploadFile = File(..., description="The short video file (max 50MB)."), # Video file as UploadFile
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API endpoint to create a new short.
    """
    # Basic file size validation (e.g., max 50MB)
    MAX_VIDEO_SIZE_MB = 50
    if video_file.size and video_file.size > MAX_VIDEO_SIZE_MB * 1024 * 1024:
        logger.warning(f"Video file too large: {video_file.size / (1024 * 1024):.2f} MB. Max allowed: {MAX_VIDEO_SIZE_MB} MB.")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Video file too large. Maximum size is {MAX_VIDEO_SIZE_MB}MB."
        )
    
    # Basic file type validation (MIME type)
    ALLOWED_VIDEO_TYPES = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/x-flv", "video/webm"]
    if video_file.content_type not in ALLOWED_VIDEO_TYPES:
        logger.warning(f"Invalid video file type: {video_file.content_type}. Allowed types: {', '.join(ALLOWED_VIDEO_TYPES)}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported video file type. Allowed types are: {', '.join(ALLOWED_VIDEO_TYPES)}"
        )

    return await shorts_controller.create_short_controller(
        description=description,
        video_file=video_file,
        current_user=current_user,
        db=db
    )

@router.get(
    "/",
    response_model=List[shorts_schema.ShortResponse],
    summary="Get a paginated list of shorts",
    description="Retrieves a list of all short video posts, with optional pagination. Includes likes and comments counts, and current user's like status."
)
async def get_shorts(
    skip: int = Query(0, ge=0, description="Number of items to skip (for pagination)."),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of items to return (for pagination)."),
    current_user: Optional[user_model.User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    API endpoint to retrieve a list of shorts.
    """
    return shorts_controller.get_shorts_controller(
        skip=skip,
        limit=limit,
        current_user=current_user,
        db=db
    )

@router.get(
    "/{short_id}",
    response_model=shorts_schema.ShortResponse,
    summary="Get a single short by ID",
    description="Retrieves the details of a specific short video post, including likes and comments counts, and current user's like status."
)
async def get_short(
    short_id: int,
    current_user: Optional[user_model.User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    API endpoint to retrieve a single short.
    """
    return shorts_controller.get_short_controller(
        short_id=short_id,
        current_user=current_user,
        db=db
    )

@router.patch(
    "/{short_id}",
    response_model=shorts_schema.ShortResponse,
    summary="Partially update a short",
    description="Allows the owner of a short to update its description or replace its video file."
)
async def update_short(
    short_id: int,
    description: Optional[str] = Form(None, max_length=500, description="The updated text description or caption for the short."),
    video_file: Optional[UploadFile] = File(None, description="Optional new video file for the short (max 50MB)."),
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API endpoint to update a short.
    """
    # Basic file size validation for new video_file
    MAX_VIDEO_SIZE_MB = 50
    if video_file and video_file.size and video_file.size > MAX_VIDEO_SIZE_MB * 1024 * 1024:
        logger.warning(f"Video file too large for update: {video_file.size / (1024 * 1024):.2f} MB. Max allowed: {MAX_VIDEO_SIZE_MB} MB.")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"New video file too large. Maximum size is {MAX_VIDEO_SIZE_MB}MB."
        )
    
    # Basic file type validation for new video_file
    ALLOWED_VIDEO_TYPES = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/x-flv", "video/webm"]
    if video_file and video_file.content_type not in ALLOWED_VIDEO_TYPES:
        logger.warning(f"Invalid video file type for update: {video_file.content_type}. Allowed types: {', '.join(ALLOWED_VIDEO_TYPES)}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported new video file type. Allowed types are: {', '.join(ALLOWED_VIDEO_TYPES)}"
        )

    return await shorts_controller.update_short_controller(
        short_id=short_id,
        description=description,
        video_file=video_file,
        current_user=current_user,
        db=db
    )

@router.delete(
    "/{short_id}",
    response_model=Dict[str, str], # Return a message on successful deletion
    status_code=status.HTTP_200_OK,
    summary="Delete a short",
    description="Allows the owner of a short to delete it. Associated video file will also be deleted."
)
async def delete_short(
    short_id: int,
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API endpoint to delete a short.
    """
    return await shorts_controller.delete_short_controller(
        short_id=short_id,
        current_user=current_user,
        db=db
    )
