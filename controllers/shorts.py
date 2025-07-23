# hive_server/controllers/shorts.py

from fastapi import Depends, HTTPException, status, Query, UploadFile, File, Form # <--- ADDED: UploadFile, File, Form
from sqlalchemy.orm import Session
import logging
from typing import List, Optional, Dict

logger = logging.getLogger("tea_n_hive_logger.shorts_controller")

from ..utils.db import get_db # Dependency for DB session
from ..utils.security import get_current_user, get_current_user_optional # Dependencies for current user
from ..schemas import shorts as shorts_schema # Short schemas for request/response
from ..models import user as user_model # User model for type hinting current_user
from ..services.shorts import ShortsService # ShortsService for business logic

# --- Shorts Controllers ---

async def create_short_controller(
    description: Optional[str] = Form(None, max_length=500, description="Optional text description or caption for the short."),
    video_file: UploadFile = File(..., description="The short video file."), # Video file as UploadFile
    current_user: user_model.User = Depends(get_current_user), # Authenticated user
    db: Session = Depends(get_db) # Database session
) -> shorts_schema.ShortResponse:
    """
    Controller to create a new short video post.
    Handles file upload and delegates to ShortsService for business logic.
    """
    logger.info(f"Received request to create short by user ID: {current_user.user_id}.")
    
    # Create a Pydantic schema object from form data
    short_data = shorts_schema.ShortCreate(description=description)

    shorts_service = ShortsService(db)
    try:
        db_short = await shorts_service.create_short(
            user_id=current_user.user_id,
            short_data=short_data,
            video_file=video_file
        )
        
        # Validate and serialize the SQLAlchemy ORM object into the Pydantic response schema.
        short_response = shorts_schema.ShortResponse.model_validate(db_short)
        
        logger.info(f"Short ID: {db_short.short_id} created successfully by user ID: {current_user.user_id}.")
        return short_response
    except HTTPException:
        raise # Re-raise HTTP exceptions (e.g., 404 Not Found, 400 Bad Request)
    except Exception as e:
        logger.exception(f"An unexpected error occurred while creating short by user ID: {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during short creation: {e}"
        )

def get_short_controller(
    short_id: int,
    current_user: Optional[user_model.User] = Depends(get_current_user_optional), # Optional for public access
    db: Session = Depends(get_db)
) -> shorts_schema.ShortResponse:
    """
    Controller to retrieve a single short by ID.
    Delegates to ShortsService for business logic.
    """
    logger.info(f"Received request to retrieve short ID: {short_id}.")
    shorts_service = ShortsService(db)
    
    # Pass current_user.user_id if authenticated, else None
    current_user_id = current_user.user_id if current_user else None
    db_short = shorts_service.get_short_by_id(short_id, current_user_id=current_user_id)
    
    if not db_short:
        logger.warning(f"Short retrieval failed: Short ID {short_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short not found."
        )
    
    short_response = shorts_schema.ShortResponse.model_validate(db_short)

    logger.info(f"Successfully retrieved short ID: {short_id}.")
    return short_response

def get_shorts_controller(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: Optional[user_model.User] = Depends(get_current_user_optional), # Optional for public access
    db: Session = Depends(get_db)
) -> List[shorts_schema.ShortResponse]:
    """
    Controller to retrieve a paginated list of shorts.
    Delegates to ShortsService for business logic.
    """
    logger.info(f"Received request to retrieve shorts (skip: {skip}, limit: {limit}).")
    shorts_service = ShortsService(db)

    # Pass current_user.user_id if authenticated, else None
    current_user_id = current_user.user_id if current_user else None
    db_shorts = shorts_service.get_shorts(skip=skip, limit=limit, current_user_id=current_user_id)
    
    # Convert list of ORM objects to list of Pydantic response models
    response_shorts = [shorts_schema.ShortResponse.model_validate(short) for short in db_shorts]

    logger.info(f"Successfully retrieved {len(response_shorts)} shorts.")
    return response_shorts

async def update_short_controller(
    short_id: int,
    description: Optional[str] = Form(None, max_length=500, description="The updated text description or caption for the short."),
    video_file: Optional[UploadFile] = File(None, description="Optional new video file for the short."), # Optional video file
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> shorts_schema.ShortResponse:
    """
    Controller to update an existing short.
    Handles optional file upload and delegates to ShortsService for business logic.
    """
    logger.info(f"Received request to update short ID: {short_id} by user ID: {current_user.user_id}.")

    # Create a Pydantic schema object from form data
    short_data = shorts_schema.ShortUpdate(description=description)

    shorts_service = ShortsService(db)
    try:
        db_short = await shorts_service.update_short(
            short_id=short_id,
            user_id=current_user.user_id,
            short_data=short_data,
            video_file=video_file # Pass the UploadFile object
        )
        
        short_response = shorts_schema.ShortResponse.model_validate(db_short)

        logger.info(f"Short ID: {short_id} updated successfully by user ID: {current_user.user_id}.")
        return short_response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred while updating short ID: {short_id} for user ID: {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during short update: {e}"
        )

async def delete_short_controller(
    short_id: int,
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Controller to delete a short.
    Delegates to ShortsService for business logic.
    Returns a success message upon completion.
    """
    logger.info(f"Received request to delete short ID: {short_id} by user ID: {current_user.user_id}.")
    shorts_service = ShortsService(db)
    try:
        await shorts_service.delete_short(short_id=short_id, user_id=current_user.user_id)
        logger.info(f"Short ID: {short_id} deleted successfully by user ID: {current_user.user_id}.")
        return {"message": f"Successfully deleted short ID {short_id}."}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred while deleting short ID: {short_id} for user ID: {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during short deletion: {e}"
        )
