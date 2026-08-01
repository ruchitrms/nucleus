import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from nucleus_api.core.security import hash_password, hash_refresh_token
from nucleus_api.services.auth_service import AuthService


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_user(email="user@example.com", password="password123"):
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = email
    user.hashed_password = hash_password(password)
    user.is_active = True
    return user


def make_token_record(user_id, raw_token, *, revoked=False, expired=False):
    record = MagicMock()
    record.user_id = user_id
    record.token_hash = hash_refresh_token(raw_token)
    record.revoked_at = datetime.now(timezone.utc) if revoked else None
    record.expires_at = (
        datetime.now(timezone.utc) - timedelta(days=1)
        if expired
        else datetime.now(timezone.utc) + timedelta(days=30)
    )
    return record


def make_service():
    user_repo = AsyncMock()
    refresh_token_repo = AsyncMock()
    return AuthService(user_repo, refresh_token_repo), user_repo, refresh_token_repo


# ── signup ────────────────────────────────────────────────────────────────────

class TestSignup:
    async def test_new_user_returns_token_response(self):
        service, user_repo, refresh_repo = make_service()
        user = make_user()
        user_repo.get_user_by_email.return_value = None
        user_repo.create_user.return_value = user
        refresh_repo.create_refresh_token.return_value = MagicMock()

        result = await service.signup("user@example.com", "password123")

        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"

    async def test_duplicate_email_raises_400(self):
        service, user_repo, _ = make_service()
        user_repo.get_user_by_email.return_value = make_user()

        with pytest.raises(HTTPException) as exc:
            await service.signup("user@example.com", "password123")

        assert exc.value.status_code == 400
        assert "already registered" in exc.value.detail

    async def test_password_is_not_stored_in_plaintext(self):
        service, user_repo, refresh_repo = make_service()
        user_repo.get_user_by_email.return_value = None
        captured = {}

        async def capture_create(email, hashed_password):
            captured["hashed"] = hashed_password
            return make_user()

        user_repo.create_user.side_effect = capture_create
        refresh_repo.create_refresh_token.return_value = MagicMock()

        await service.signup("user@example.com", "plaintext123")

        assert captured["hashed"] != "plaintext123"
        assert captured["hashed"].startswith("$2b$")


# ── login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    async def test_correct_credentials_return_token_response(self):
        service, user_repo, refresh_repo = make_service()
        user = make_user(password="password123")
        user_repo.get_user_by_email.return_value = user
        refresh_repo.create_refresh_token.return_value = MagicMock()

        result = await service.login("user@example.com", "password123")

        assert result.access_token
        assert result.refresh_token

    async def test_unknown_email_raises_401(self):
        service, user_repo, _ = make_service()
        user_repo.get_user_by_email.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.login("ghost@example.com", "password123")

        assert exc.value.status_code == 401

    async def test_wrong_password_raises_401(self):
        service, user_repo, _ = make_service()
        user_repo.get_user_by_email.return_value = make_user(password="correct")

        with pytest.raises(HTTPException) as exc:
            await service.login("user@example.com", "wrong")

        assert exc.value.status_code == 401

    async def test_wrong_email_and_wrong_password_return_identical_errors(self):
        """Both failure modes must produce the same response — don't reveal which part failed."""
        service, user_repo, _ = make_service()

        user_repo.get_user_by_email.return_value = None
        with pytest.raises(HTTPException) as exc1:
            await service.login("ghost@example.com", "anything")

        user_repo.get_user_by_email.return_value = make_user(password="correct")
        with pytest.raises(HTTPException) as exc2:
            await service.login("user@example.com", "wrong")

        assert exc1.value.status_code == exc2.value.status_code
        assert exc1.value.detail == exc2.value.detail


# ── refresh_access_token ──────────────────────────────────────────────────────

class TestRefreshAccessToken:
    async def test_valid_token_returns_new_token_response(self):
        service, _, refresh_repo = make_service()
        raw_token = "valid-raw-token"
        record = make_token_record(uuid.uuid4(), raw_token)
        refresh_repo.get_refresh_token.return_value = record
        refresh_repo.create_refresh_token.return_value = MagicMock()

        result = await service.refresh_access_token(raw_token)

        assert result.access_token
        assert result.refresh_token

    async def test_old_token_is_revoked_on_refresh(self):
        """Token rotation: using a refresh token must immediately invalidate it."""
        service, _, refresh_repo = make_service()
        raw_token = "rotate-me"
        record = make_token_record(uuid.uuid4(), raw_token)
        refresh_repo.get_refresh_token.return_value = record
        refresh_repo.create_refresh_token.return_value = MagicMock()

        await service.refresh_access_token(raw_token)

        refresh_repo.revoke_refresh_token.assert_awaited_once()

    async def test_token_not_found_raises_401(self):
        service, _, refresh_repo = make_service()
        refresh_repo.get_refresh_token.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.refresh_access_token("nonexistent")

        assert exc.value.status_code == 401

    async def test_revoked_token_raises_401(self):
        service, _, refresh_repo = make_service()
        raw_token = "already-revoked"
        refresh_repo.get_refresh_token.return_value = make_token_record(
            uuid.uuid4(), raw_token, revoked=True
        )

        with pytest.raises(HTTPException) as exc:
            await service.refresh_access_token(raw_token)

        assert exc.value.status_code == 401

    async def test_expired_token_raises_401(self):
        service, _, refresh_repo = make_service()
        raw_token = "expired-token"
        refresh_repo.get_refresh_token.return_value = make_token_record(
            uuid.uuid4(), raw_token, expired=True
        )

        with pytest.raises(HTTPException) as exc:
            await service.refresh_access_token(raw_token)

        assert exc.value.status_code == 401


# ── logout ────────────────────────────────────────────────────────────────────

class TestLogout:
    async def test_logout_revokes_the_correct_token(self):
        service, _, refresh_repo = make_service()
        raw_token = "logout-token"

        await service.logout(raw_token)

        refresh_repo.revoke_refresh_token.assert_awaited_once_with(
            hash_refresh_token(raw_token)
        )

    async def test_logout_with_unknown_token_does_not_raise(self):
        """revoke_refresh_token no-ops on unknown tokens — logout should never error."""
        service, _, refresh_repo = make_service()
        refresh_repo.revoke_refresh_token.return_value = None

        await service.logout("unknown-token")  # must not raise
