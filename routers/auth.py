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
def register(
    user_data: user_schema.UserCreate,
    response: user_schema.UserWithProfileResponse = Depends(auth_controller.register_user_controller)
):
    return response

@router.post(
    "/token",
    response_model=Token, # Response model is the Token schema
    summary="Authenticate user and get access token",
    description="Authenticates a user with email/username and password, returning a JWT access token."
)
# The login endpoint now delegates all logic to login_for_access_token_controller
async def login_for_access_token(
    # Pass the form_data and db session directly to the controller
    # The controller itself is a dependency that returns the Token
    response: Token = Depends(auth_controller.login_for_access_token_controller)
):
    """
    API endpoint for user login.
    Delegates the authentication and token generation logic to the auth_controller.
    """
    return response