# Hive-server/routers/auth.py

from fastapi import APIRouter, Depends
from fastapi import status
from ..controllers import auth as auth_controller # Import controller functions
from ..schemas import user as user_schema # Import schemas for request/response models

# Initialize FastAPI APIRouter for authentication-related routes
router = APIRouter(
    prefix="/auth", # All routes defined here will be prefixed with /auth
    tags=["Authentication"] # Group these routes under "Authentication" in Swagger UI
)

@router.post(
    "/register",
    response_model=user_schema.UserResponse, # Define the response schema
    status_code=status.HTTP_201_CREATED, # Set the HTTP status code for successful creation
    summary="Register a new user", # Short description for Swagger UI
    description="Creates a new user account with email and password." # Detailed description
)
def register(
    user_data: user_schema.UserCreate, # Request body validated by UserCreate schema
    # The controller function is injected as a dependency, handling the core logic
    response: user_schema.UserResponse = Depends(auth_controller.register_user_controller)
):
    """
    Handles the user registration request.
    Delegates the core logic to the `register_user_controller`.
    """
    return response

# Future: Add routes for /auth/login, /auth/forgot-password, etc.