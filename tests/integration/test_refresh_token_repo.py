import uuid
from datetime import datetime, timedelta, timezone

from nucleus_api.repositories.refresh_token_repo import RefreshTokenRepository
from nucleus_api.repositories.user_repo import UserRepository


async def _create_user(db_session):
    """Create a throw-away user to satisfy the foreign key on refresh_tokens."""
    repo = UserRepository(db_session)
    return await repo.create_user(f"{uuid.uuid4()}@example.com", "hash")


class TestCreateRefreshToken:
    async def test_stores_record_with_correct_fields(self, db_session):
        user = await _create_user(db_session)
        repo = RefreshTokenRepository(db_session)
        expires = datetime.now(timezone.utc) + timedelta(days=30)

        record = await repo.create_refresh_token(user.id, "myhash", expires)

        assert record.user_id == user.id
        assert record.token_hash == "myhash"
        assert record.revoked_at is None

    async def test_revoked_at_is_null_on_creation(self, db_session):
        user = await _create_user(db_session)
        repo = RefreshTokenRepository(db_session)
        expires = datetime.now(timezone.utc) + timedelta(days=30)

        record = await repo.create_refresh_token(user.id, "fresh", expires)

        assert record.revoked_at is None


class TestGetRefreshToken:
    async def test_returns_record_for_existing_hash(self, db_session):
        user = await _create_user(db_session)
        repo = RefreshTokenRepository(db_session)
        expires = datetime.now(timezone.utc) + timedelta(days=30)
        await repo.create_refresh_token(user.id, "lookup-hash", expires)

        record = await repo.get_refresh_token("lookup-hash")

        assert record is not None
        assert record.token_hash == "lookup-hash"

    async def test_returns_none_for_unknown_hash(self, db_session):
        repo = RefreshTokenRepository(db_session)
        result = await repo.get_refresh_token("does-not-exist")
        assert result is None


class TestRevokeRefreshToken:
    async def test_sets_revoked_at_timestamp(self, db_session):
        user = await _create_user(db_session)
        repo = RefreshTokenRepository(db_session)
        expires = datetime.now(timezone.utc) + timedelta(days=30)
        await repo.create_refresh_token(user.id, "to-revoke", expires)

        await repo.revoke_refresh_token("to-revoke")

        record = await repo.get_refresh_token("to-revoke")
        assert record.revoked_at is not None
        assert isinstance(record.revoked_at, datetime)

    async def test_revoked_at_is_recent(self, db_session):
        user = await _create_user(db_session)
        repo = RefreshTokenRepository(db_session)
        expires = datetime.now(timezone.utc) + timedelta(days=30)
        await repo.create_refresh_token(user.id, "recent-revoke", expires)

        before = datetime.now(timezone.utc)
        await repo.revoke_refresh_token("recent-revoke")

        record = await repo.get_refresh_token("recent-revoke")
        # revoked_at should be within a few seconds of now
        assert record.revoked_at >= before

    async def test_does_not_raise_for_nonexistent_token(self, db_session):
        """Revoking an unknown token is a no-op — logout must never error."""
        repo = RefreshTokenRepository(db_session)
        await repo.revoke_refresh_token("ghost-hash")  # must not raise
