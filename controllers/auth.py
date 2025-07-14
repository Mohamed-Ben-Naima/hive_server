# Hive-server/controllers/auth.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..utils.db import get_db # Import database session dependency
from ..schemas import user as user_schema # Import user schemas
from ..services.user import UserService # Import user service logic

def register_user_controller(
    user_data: user_schema.UserCreate, # Input validated by Pydantic
    db: Session = Depends(get_db) # Database session dependency injection
) -> user_schema.UserResponse:
    """
    Controller function for handling user registration requests.
    It orchestrates data validation, calls the appropriate service,
    and formats the response.
    """
    user_service = UserService(db) # Initialize the user service with the DB session
    try:
        # Call the service layer to create the user
        new_user = user_service.create_user(user_data)
        # Validate and return the response using the Pydantic schema
        return user_schema.UserResponse.model_validate(new_user)
    except HTTPException as e:
        # Re-raise HTTPExceptions (e.g., 409 Conflict for existing email)
        raise e
    except Exception as e:
        # Catch any other unexpected errors and return a generic 500 error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during registration: {e}"
        )

# Future: Add controller functions for login, password reset, etc.