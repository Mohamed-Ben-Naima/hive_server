# Hive-server/controllers/auth.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging # <-- NEW: Import logging

# Get logger instance for this module
logger = logging.getLogger("trader_hive_logger.auth_controller")

from ..utils.db import get_db
from ..schemas import user as user_schema
from ..services.user import UserService

def register_user_controller(
    user_data: user_schema.UserCreate,
    db: Session = Depends(get_db)
) -> user_schema.UserWithProfileResponse:
    logger.info(f"Received registration request for email: {user_data.email}, username: {user_data.username}")
    user_service = UserService(db)
    try:
        new_user = user_service.create_user(user_data)
        response_data = user_schema.UserWithProfileResponse.model_validate(new_user)
        response_data.message = "User registered successfully!"
        logger.info(f"User {user_data.email} registered successfully.")
        return response_data
    except HTTPException as e:
        logger.warning(f"Registration failed for {user_data.email} with HTTP error: {e.detail} (Status: {e.status_code})")
        raise e
    except Exception as e:
        logger.exception(f"An unexpected error occurred in register_user_controller for {user_data.email}.") # logger.exception logs traceback
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during registration: {e}"
        )