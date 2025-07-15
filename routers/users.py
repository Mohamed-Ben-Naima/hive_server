# hive_server/routers/users.py

# --- Standard Library Imports ---
import logging

# --- External Library Imports ---
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

# --- Internal Project Imports ---
from ..utils.db import get_db # For dependency injection
from ..utils.security import get_current_user # The key dependency for authentication
from ..schemas.user import UserWithProfileResponse # For response model
from ..controllers import user as user_controller # Import the user controller
from ..models.user import User as UserModel # Your SQLAlchemy User model for type hinting

# Get logger instance for this module
logger = logging.getLogger("tea_n_hive_logger.users_router")

# Initialize FastAPI router for user-related endpoints
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get(
    "/me",
    response_model=UserWithProfileResponse, # Returns user details with profile
    summary="Get current user's profile",
    description="Retrieves the detailed profile information for the currently authenticated user."
)
async def read_current_user_profile(
    # get_current_user validates the token and fetches the user from DB (with profile loaded)
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db) # Pass db session to controller if needed there
):
    """
    API endpoint to get the current authenticated user's details and profile.
    Requires a valid JWT access token in the Authorization header.
    """
    # Delegate to the user controller to process and return the user profile
    # The current_user object (SQLAlchemy model) is passed directly to the controller
    return user_controller.get_current_user_profile_controller(current_user=current_user, db=db)

# Add other user-related router endpoints here as needed (e.g., PUT /users/me for updates)
