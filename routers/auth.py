# Hive-server/routers/auth.py

import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, status
from ..controllers import auth as auth_controller
from ..schemas import user as user_schema

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm # Import this for form data

from sqlalchemy.orm import Session

from ..utils.db import get_db
from ..utils.security import create_access_token, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from ..schemas.auth import Token # Import Token and UserCreate schemas
from ..schemas.user import UserCreate # Import UserCreate schemas
from ..services.user import UserService # Import UserService

# Get logger instance for this module
logger = logging.getLogger("tea_n_hive_logger.auth")

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post(
    "/register",
    response_model=user_schema.UserWithProfileResponse, # <-- NEW: Use UserWithProfileResponse
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with email, username, and password, and initializes their profile."
)
async def register( # Changed to async as controllers might be async, or just good practice
    user_data: user_schema.UserCreate, # Direct request body parameter
    db: Session = Depends(get_db) # Direct dependency injection for the database session
):
    """
    API endpoint for user registration.
    Delegates the registration logic to the auth_controller.
    """
    # Explicitly call the controller and pass necessary arguments
    return auth_controller.register_user_controller(user_data=user_data, db=db)

@router.post(
    "/token",
    response_model=Token, # Response model is the Token schema
    summary="Authenticate user and get access token",
    description="Authenticates a user with email/username and password, returning a JWT access token."
)
# The login endpoint now delegates all logic to login_for_access_token_controller
async def login_for_access_token( # Changed to async
    form_data: OAuth2PasswordRequestForm = Depends(), # Direct request form data parameter
    db: Session = Depends(get_db) # Direct dependency injection for the database session
):
    """
    API endpoint for user login.
    Delegates the authentication and token generation logic to the auth_controller.
    """
    # Explicitly call the controller and pass necessary arguments
    return auth_controller.login_for_access_token_controller(form_data=form_data, db=db)

# <--- NEW: Endpoint for initiating password reset (Forgot Password) ---
@router.post(
    "/forgot-password",
    response_model=dict, # Returns a generic success message for security
    summary="Request password reset link",
    description="Sends a password reset link to the user's email if an account exists. Always returns a success message for security reasons (to prevent email enumeration)."
)
async def forgot_password(
    request_data: user_schema.ForgotPasswordRequest, # Expects email
    db: Session = Depends(get_db)
):
    """
    API endpoint to initiate the password reset process.
    The client provides the user's email. A password reset link (containing a JWT token)
    will be sent to the email address if an account exists.
    """
    # Delegate to the auth controller
    return await auth_controller.forgot_password_controller(request_data=request_data, db=db)

# <--- NEW: Endpoint for resetting password with token ---
@router.post(
    "/reset-password",
    response_model=dict, # Returns a simple success message
    summary="Reset password using token",
    description="Resets the user's password using a valid password reset token received via email."
)
async def reset_password(
    request_data: user_schema.ResetPasswordRequest, # Expects token, new_password, confirm_new_password
    db: Session = Depends(get_db)
):
    """
    API endpoint to complete the password reset process.
    The client provides the password reset token and the new password.
    """
    # Delegate to the auth controller
    return auth_controller.reset_password_controller(request_data=request_data, db=db)