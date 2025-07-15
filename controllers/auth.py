# Hive-server/controllers/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging # <-- NEW: Import logging

# Get logger instance for this module
logger = logging.getLogger("tea_n_hive_logger.auth_controller") # Corrected logger name

from ..utils.db import get_db # Relative import
from ..schemas import user as user_schema # Relative import
from ..schemas.auth import Token # Relative import
from ..services.user import UserService # Relative import
from ..utils import security # Relative import
from ..utils.app_setup import ACCESS_TOKEN_EXPIRE_MINUTES # Relative import

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
    
def login_for_access_token_controller(
    form_data: OAuth2PasswordRequestForm = Depends(), # Input from the client
    db: Session = Depends(get_db)
) -> Token: # This controller will return a Token schema object
    """
    Controller function to handle user authentication and JWT token generation.
    Contains the core business logic for login.
    """
    user_service = UserService(db)
    user = user_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        logger.warning(f"Login failed for {form_data.username}: Invalid credentials.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # <--- NEW: Update last_login timestamp after successful authentication ---
    user_service.update_user_last_login(user)
    # --- END NEW ---
    
    # Ensure the user object has a profile and extract username
    # This assumes that for an authenticated user, a profile will always exist.
    # If a profile might not exist, you'd need to handle user.profile being None.
    username_for_token = user.profile.username if user.profile else None
    if username_for_token is None:
        logger.error(f"Authenticated user {user.email} (ID: {user.user_id}) has no associated profile or username.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User profile information missing."
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token_data = {
        "user_id": user.user_id,
        "email": user.email,
        "username": user.profile.username if user.profile else None
    }
    access_token = security.create_access_token(
        data=access_token_data,
        expires_delta=access_token_expires
    )
    logger.info(f"User {user.email} successfully logged in and received access token.")

    # Explicitly construct UserForTokenResponse from the SQLAlchemy user object
    # Pulling username from user.profile
    user_for_token_response = user_schema.UserForTokenResponse(
        user_id=user.user_id,
        email=user.email,
        username=username_for_token, # Use the extracted username
    )
    
    # Return the Token object with user info, using the new UserForTokenResponse schema
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_for_token_response # <--- CHANGED: Use UserForTokenResponse
    )