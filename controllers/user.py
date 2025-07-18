# hive_server/controllers/user.py

# --- Standard Library Imports ---
import logging

# --- External Library Imports ---
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated # For cleaner dependency injection type hints

# --- Internal Project Imports ---
from ..utils.db import get_db
from ..schemas.user import UserWithProfileResponse, ProfileUpdate # For response model
from ..models.user import User as UserModel # Your SQLAlchemy User model
from ..services.user import UserService # To interact with user data

# Get logger instance for this module
logger = logging.getLogger("tea_n_hive_logger.user_controller")

# --- Controller for fetching current user's details ---
# This function receives the 'current_user' (an SQLAlchemy User model instance)
# which is provided by the get_current_user dependency in security.py
def get_current_user_profile_controller(
    current_user: Annotated[UserModel, Depends()], # This dependency will be injected by the router
    db: Session = Depends(get_db) # Also need the DB session for potential future use or explicit refresh
) -> UserWithProfileResponse:
    """
    Controller function to get the details of the currently authenticated user
    including their profile.
    """
    logger.info(f"Fetching profile for authenticated user: {current_user.email} (ID: {current_user.user_id})")
    
    # Ensure the profile is loaded. get_current_user in security.py should already do this
    # via UserService.get_user_by_id with joinedload.
    # If for some reason it's not, you might need to refresh or re-fetch here,
    # but ideally, the user object passed here already has the profile.
    
    # Validate the SQLAlchemy user model (which includes profile) into the Pydantic response schema
    try:
        response_data = UserWithProfileResponse.model_validate(current_user)
        logger.debug(f"Successfully prepared user profile response for {current_user.email}.")
        return response_data
    except Exception as e:
        logger.exception(f"Error validating user model into UserWithProfileResponse for user {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user profile: {e}"
        )

# Add other user-related controller functions here as needed (e.g., update_user_profile)
# <--- NEW: Controller for updating current user's profile ---
def update_user_profile_controller(
    current_user: Annotated[UserModel, Depends()], # The authenticated user whose profile will be updated
    profile_data: ProfileUpdate, # The partial update data from the request body
    db: Session = Depends(get_db)
) -> UserWithProfileResponse:
    """
    Controller function to update the profile of the currently authenticated user.
    """
    logger.info(f"Received profile update request for user: {current_user.email} (ID: {current_user.user_id})")

    user_service = UserService(db)
    try:
        # Call the UserService method to perform the profile update
        updated_user = user_service.update_user_profile(user=current_user, profile_data=profile_data)
        
        # Validate the updated SQLAlchemy user model into the Pydantic response schema
        response_data = UserWithProfileResponse.model_validate(updated_user)
        response_data.message = "Profile updated successfully!" # Add a success message
        logger.info(f"Profile for user {current_user.email} updated successfully.")
        return response_data
    except HTTPException: # Re-raise HTTPExceptions (e.g., 409 Conflict from service)
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred during profile update for user {current_user.user_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile due to a server error: {e}"
        )