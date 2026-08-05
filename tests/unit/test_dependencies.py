import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nucleus_api.core.dependencies import get_current_user
from nucleus_api.core.exceptions import UnauthorizedException
from nucleus_api.core.security import create_access_token


def make_credentials(token: str):
    creds = MagicMock()
    creds.credentials = token
    return creds


class TestGetCurrentUser:
    async def test_valid_token_returns_user(self):
        user_id = uuid.uuid4()
        credentials = make_credentials(create_access_token(user_id))
        mock_user = MagicMock(id=user_id)

        with patch("nucleus_api.core.dependencies.UserRepository") as mock_repo_cls:
            mock_repo_cls.return_value.get_user_by_id = AsyncMock(return_value=mock_user)
            result = await get_current_user(credentials=credentials, db=AsyncMock())

        assert result == mock_user

    async def test_invalid_token_raises_unauthorized(self):
        credentials = make_credentials("not.a.valid.token")

        with pytest.raises(UnauthorizedException):
            await get_current_user(credentials=credentials, db=AsyncMock())

    async def test_expired_token_raises_unauthorized(self):
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        from nucleus_api.core.config import settings

        expired_token = jwt.encode(
            {"sub": str(uuid.uuid4()), "exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
            settings.secret_key,
            algorithm=settings.algorithm,
        )
        credentials = make_credentials(expired_token)

        with pytest.raises(UnauthorizedException):
            await get_current_user(credentials=credentials, db=AsyncMock())

    async def test_user_not_found_raises_unauthorized(self):
        credentials = make_credentials(create_access_token(uuid.uuid4()))

        with patch("nucleus_api.core.dependencies.UserRepository") as mock_repo_cls:
            mock_repo_cls.return_value.get_user_by_id = AsyncMock(return_value=None)

            with pytest.raises(UnauthorizedException):
                await get_current_user(credentials=credentials, db=AsyncMock())
