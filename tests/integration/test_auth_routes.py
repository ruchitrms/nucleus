import pytest
from httpx import ASGITransport, AsyncClient

from nucleus_api.db.session import get_db
from nucleus_api.main import app


@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _signup_token(client: AsyncClient, email: str, password: str = "pass123") -> str:
    r = await client.post("/api/v1/auth/signup", json={"email": email, "password": password})
    return r.json()["access_token"]


class TestSignupRoute:
    async def test_returns_200_and_tokens(self, client):
        r = await client.post("/api/v1/auth/signup", json={"email": "new@example.com", "password": "pass123"})
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    async def test_duplicate_email_returns_409(self, client):
        await client.post("/api/v1/auth/signup", json={"email": "dup@example.com", "password": "pass123"})
        r = await client.post("/api/v1/auth/signup", json={"email": "dup@example.com", "password": "pass123"})
        assert r.status_code == 409

    async def test_invalid_email_format_returns_422(self, client):
        r = await client.post("/api/v1/auth/signup", json={"email": "notanemail", "password": "pass123"})
        assert r.status_code == 422


class TestLoginRoute:
    async def test_returns_200_with_correct_credentials(self, client):
        await client.post("/api/v1/auth/signup", json={"email": "login@example.com", "password": "pass123"})
        r = await client.post("/api/v1/auth/login", json={"email": "login@example.com", "password": "pass123"})
        assert r.status_code == 200
        assert "access_token" in r.json()

    async def test_wrong_password_returns_401(self, client):
        await client.post("/api/v1/auth/signup", json={"email": "wp@example.com", "password": "correct"})
        r = await client.post("/api/v1/auth/login", json={"email": "wp@example.com", "password": "wrong"})
        assert r.status_code == 401

    async def test_unknown_email_returns_401(self, client):
        r = await client.post("/api/v1/auth/login", json={"email": "ghost@example.com", "password": "any"})
        assert r.status_code == 401

    async def test_wrong_and_unknown_return_same_error_message(self, client):
        """Both failure modes must return the same detail to avoid leaking info."""
        await client.post("/api/v1/auth/signup", json={"email": "sameErr@example.com", "password": "correct"})
        r1 = await client.post("/api/v1/auth/login", json={"email": "ghost@example.com", "password": "x"})
        r2 = await client.post("/api/v1/auth/login", json={"email": "sameErr@example.com", "password": "wrong"})
        assert r1.json()["detail"] == r2.json()["detail"]


class TestGetMeRoute:
    async def test_returns_200_with_correct_user_fields(self, client):
        token = await _signup_token(client, "me@example.com")
        r = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == "me@example.com"
        assert "id" in body
        assert body["is_active"] is True

    async def test_returns_403_without_token(self, client):
        r = await client.get("/api/v1/users/me")
        assert r.status_code == 403

    async def test_returns_401_with_invalid_token(self, client):
        r = await client.get("/api/v1/users/me", headers={"Authorization": "Bearer not.a.real.token"})
        assert r.status_code == 401
