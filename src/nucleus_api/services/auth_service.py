
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from nucleus_api.core.security import (
    create_access_token, create_refresh_token,
    hash_password, hash_refresh_token, verify_password
)
from nucleus_api.repositories.refresh_token_repo import RefreshTokenRepository
from nucleus_api.repositories.user_repo import UserRepository
from nucleus_api.schemas.user import TokenResponse

REFRESH_TOKEN_EXPIRE_DAYS = 30


class AuthService:
    def __init__(self, user_repo: UserRepository, refresh_token_repo: RefreshTokenRepository):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo

    async def signup(self, email: str, password: str) -> TokenResponse:
        if await self.user_repo.get_user_by_email(email):
            raise HTTPException(status_code=400, detail="Email already registered")
        user = await self.user_repo.create_user(email, hash_password(password))
        return await self._issue_tokens(user.id)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.user_repo.get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            # same error for both cases — don't reveal which part was wrong
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return await self._issue_tokens(user.id)

    async def refresh_access_token(self, raw_token: str) -> TokenResponse:
        token_hash = hash_refresh_token(raw_token)
        record = await self.refresh_token_repo.get_refresh_token(token_hash)
        if not record or record.revoked_at is not None:
            raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")
        if record.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Refresh token expired")
        await self.refresh_token_repo.revoke_refresh_token(token_hash)
        return await self._issue_tokens(record.user_id)

    async def logout(self, raw_token: str) -> None:
        await self.refresh_token_repo.revoke_refresh_token(hash_refresh_token(raw_token))

    async def _issue_tokens(self, user_id) -> TokenResponse:
        raw_refresh = create_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        await self.refresh_token_repo.create_refresh_token(
            user_id, hash_refresh_token(raw_refresh), expires_at
        )
        return TokenResponse(
            access_token=create_access_token(user_id),
            refresh_token=raw_refresh,
            token_type="bearer"
        )