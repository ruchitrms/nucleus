import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from nucleus_api.repositories.user_repo import UserRepository


class TestCreateUser:
    async def test_stores_email_and_hashed_password(self, db_session):
        repo = UserRepository(db_session)
        user = await repo.create_user("alice@example.com", "hashed_pw")
        assert user.email == "alice@example.com"
        assert user.hashed_password == "hashed_pw"

    async def test_assigns_uuid_as_id(self, db_session):
        repo = UserRepository(db_session)
        user = await repo.create_user("bob@example.com", "hash")
        assert isinstance(user.id, uuid.UUID)

    async def test_is_active_defaults_to_true(self, db_session):
        repo = UserRepository(db_session)
        user = await repo.create_user("carol@example.com", "hash")
        assert user.is_active is True

    async def test_duplicate_email_raises_integrity_error(self, db_session):
        """The UNIQUE constraint on email must be enforced at the DB level."""
        repo = UserRepository(db_session)
        await repo.create_user("dup@example.com", "hash1")
        with pytest.raises(IntegrityError):
            await repo.create_user("dup@example.com", "hash2")


class TestGetUserByEmail:
    async def test_returns_user_for_existing_email(self, db_session):
        repo = UserRepository(db_session)
        created = await repo.create_user("dave@example.com", "hash")
        found = await repo.get_user_by_email("dave@example.com")
        assert found is not None
        assert found.id == created.id

    async def test_returns_none_for_unknown_email(self, db_session):
        repo = UserRepository(db_session)
        result = await repo.get_user_by_email("nobody@example.com")
        assert result is None

    async def test_lookup_is_case_sensitive(self, db_session):
        """Postgres text comparison is case-sensitive — 'User@' != 'user@'."""
        repo = UserRepository(db_session)
        await repo.create_user("Case@example.com", "hash")
        result = await repo.get_user_by_email("case@example.com")
        assert result is None


class TestGetUserById:
    async def test_returns_user_for_existing_id(self, db_session):
        repo = UserRepository(db_session)
        created = await repo.create_user("eve@example.com", "hash")
        found = await repo.get_user_by_id(created.id)
        assert found is not None
        assert found.email == "eve@example.com"

    async def test_returns_none_for_unknown_id(self, db_session):
        repo = UserRepository(db_session)
        result = await repo.get_user_by_id(uuid.uuid4())
        assert result is None
