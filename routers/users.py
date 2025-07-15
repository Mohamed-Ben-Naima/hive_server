# Hive-server/routers/users.py

from fastapi import APIRouter, Depends, status
from ..schemas import user as user_schema # Relative import
from ..utils.security import get_current_user # Relative import
from ..models.user import User # Relative import

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get(
    "/me",
    response_model=user_schema.UserWithProfileResponse,
    summary="Get current authenticated user's details",
    description="Retrieves the details of the currently authenticated user, including their profile."
)
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    return user_schema.UserWithProfileResponse.model_validate(current_user)