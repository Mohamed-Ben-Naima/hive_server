# Hive-server/controllers/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging 

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
        logger.exception(f"An unexpected error occurred in register_user_controller for {user_data.email}.")
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
    
    # Update last_login timestamp after successful authentication
    user_service.update_user_last_login(user)
    
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

# <--- NEW: Controller for initiating password reset ---
async def forgot_password_controller(
    request_data: user_schema.ForgotPasswordRequest,
    db: Session = Depends(get_db)
) -> dict: # Returns a simple success message for security
    """
    Controller function to handle password reset request (sending email with token).
    """
    logger.info(f"Received forgot password request for email: {request_data.email}")
    user_service = UserService(db)
    
    # In a real app, base_url would come from config or request headers.
    # For now, let's use a placeholder.
    # When deployed, this should be your frontend's base URL.
    base_url = "http://localhost:8000" # Placeholder for your frontend's base URL

    try:
        # Delegate to service. Service handles not revealing if email exists.
        await user_service.initiate_password_reset(email=request_data.email, base_url=base_url)
        logger.info(f"Forgot password process initiated for {request_data.email}. Message sent (or simulated).")
        # Always return a generic success message to prevent email enumeration attacks.
        return {"message": "If an account with that email exists, a password reset link has been sent."}
    except Exception as e:
        logger.exception(f"An unexpected error occurred during forgot password request for {request_data.email}.")
        # Still return a generic success message even on server-side error for security.
        return {"message": "If an account with that email exists, a password reset link has been sent."}

# <--- NEW: Controller for resetting password with token ---
def reset_password_controller(
    request_data: user_schema.ResetPasswordRequest,
    db: Session = Depends(get_db)
) -> dict: # Returns a simple success message
    """
    Controller function to handle password reset using a token.
    """
    logger.info("Received password reset request with token.")
    user_service = UserService(db)

    try:
        # Call the UserService method to perform the password reset
        user_service.reset_user_password(token=request_data.token, new_password=request_data.new_password)
        
        logger.info("Password successfully reset via token.")
        return {"message": "Password has been reset successfully. You can now log in with your new password."}
    except HTTPException: # Re-raise HTTPExceptions (e.g., for invalid/expired token, user not found)
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred during password reset with token.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password due to a server error: {e}"
        )