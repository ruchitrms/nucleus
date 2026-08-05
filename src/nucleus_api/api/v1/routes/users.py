from fastapi import APIRouter
from fastapi import Depends
from nucleus_api.core.dependencies import get_current_user
from nucleus_api.models.user import User
from nucleus_api.schemas.user import UserResponse
router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_endpoint(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)