import uuid
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from nucleus_api.core.exceptions import UnauthorizedException
from nucleus_api.core.security import decode_access_token
from nucleus_api.db.session import get_db
from nucleus_api.models.user import User
from nucleus_api.repositories.user_repo import UserRepository

# HTTPBearer shows a simple "token" input in Swagger instead of an OAuth2 username/password form
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedException("Invalid or expired token")
    user_id = uuid.UUID(payload["sub"])
    user = await UserRepository(db).get_user_by_id(user_id)
    if user is None:
        raise UnauthorizedException("Invalid or expired token")
    return user