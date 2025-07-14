# Hive-server/routers/auth.py

from fastapi import APIRouter, Depends, status
from ..controllers import auth as auth_controller
from ..schemas import user as user_schema

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