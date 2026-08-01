from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from nucleus_api.db.session import get_db
from nucleus_api.repositories.refresh_token_repo import RefreshTokenRepository
from nucleus_api.repositories.user_repo import UserRepository
from nucleus_api.schemas.user import RefreshTokenRequest, TokenResponse, UserCreate, UserLogin
from nucleus_api.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=TokenResponse)
async def signup(body: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(UserRepository(db), RefreshTokenRepository(db))
    return await service.signup(body.email, body.password)

@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    service = AuthService(UserRepository(db), RefreshTokenRepository(db))
    return await service.login(body.email, body.password)   

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(UserRepository(db), RefreshTokenRepository(db))
    return await service.refresh_access_token(body.refresh_token)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(UserRepository(db), RefreshTokenRepository(db))
    await service.logout(body.refresh_token)