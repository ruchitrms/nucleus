from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from nucleus_api.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db_session: AsyncSession):
            self.db_session = db_session

    async def create_refresh_token(self, user_id, token_hash, expires_at):
        refresh_token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db_session.add(refresh_token)
        await self.db_session.commit()
        await self.db_session.refresh(refresh_token)
        return refresh_token

    async def get_refresh_token(self, token):
        result = await self.db_session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token)
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_hash: str) -> None:
        result = await self.db_session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        refresh_token = result.scalar_one_or_none()
        if refresh_token:
            refresh_token.revoked_at = datetime.now(timezone.utc)
            await self.db_session.commit()