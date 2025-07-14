# Hive-server/controllers/auth.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..utils.db import get_db
from ..schemas import user as user_schema
from ..services.user import UserService

def register_user_controller(
    user_data: user_schema.UserCreate,
    db: Session = Depends(get_db)
) -> user_schema.UserWithProfileResponse:
    user_service = UserService(db)
    try:
        new_user = user_service.create_user(user_data)
        # Create the response model instance and add the success message
        response_data = user_schema.UserWithProfileResponse.model_validate(new_user)
        response_data.message = "User registered successfully!" # <-- NEW: Set the success message
        return response_data
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during registration: {e}"
        )