# Week 1–2 Build Plan: Auth, Validation, Error Handling

## Context
Project: Nucleus — e-commerce backend (FastAPI + PostgreSQL + Redis)
Start date: Monday July 27, 2026
Chat session may not persist — this file captures everything needed to resume.

---

## Environment Recap
- Python 3.11, venv at `.venv/` — activate with `source .venv/bin/activate`
- PostgreSQL running in Docker — start with `docker compose up -d` from project root
- `.env` file exists at project root with all required values
- Dependencies installed via `pip install -r requirements/dev.txt`

---

## Build Order

### ✅ Step 1 — PostgreSQL via Docker
`docker-compose.yml` created and container running.
Verify anytime: `docker compose ps` → should show `db` as running.

### ✅ Step 2 — `core/config.py`
Pydantic-settings `Settings` class reads all env vars from `.env`.
All fields lowercase (Python convention). `settings = Settings()` singleton at bottom.
Verified working: `python -c "from src.nucleus_api.core.config import settings; print(settings.postgres_host)"`

### ✅ Step 3 — `db/base.py` + `db/session.py`
- `base.py`: SQLAlchemy `DeclarativeBase` — all models inherit from this ✅
- `session.py`: async engine + `async_sessionmaker` + `get_db()` FastAPI dependency ✅
- Why async: FastAPI is async-native; blocking DB calls would negate the benefit (same as blocking main thread in Android)

### ⬜ Step 4 — `models/user.py`
SQLAlchemy ORM model for the `users` table. Columns:
- `id` (UUID, primary key)
- `email` (unique, indexed)
- `hashed_password` (str)
- `is_active` (bool, default True)
- `created_at`, `updated_at` (timestamps)

Also need `models/refresh_token.py`:
- `id`, `user_id` (FK), `token_hash`, `expires_at`, `revoked_at`, `created_at`

### ⬜ Step 5 — Alembic setup + first migration
- `alembic init alembic` in project root
- Configure `alembic.ini` + `alembic/env.py` to use async engine and import all models
- `alembic revision --autogenerate -m "create users and refresh tokens tables"`
- `alembic upgrade head` — creates tables in the running PostgreSQL container

### ⬜ Step 6 — `schemas/user.py`
Pydantic schemas (not ORM models — these are request/response shapes):
- `UserCreate`: email + password (input for signup)
- `UserLogin`: email + password (input for login)
- `UserResponse`: id + email + is_active (never expose hashed_password in response)
- `TokenResponse`: access_token + refresh_token + token_type

### ⬜ Step 7 — `repositories/user_repo.py`
All DB queries for users live here. Services call this — never raw DB calls in services.
- `get_by_email(email)` → User or None
- `create(email, hashed_password)` → User
- `get_by_id(id)` → User or None

Also `repositories/refresh_token_repo.py`:
- `create(user_id, token_hash, expires_at)` → RefreshToken
- `get_by_hash(token_hash)` → RefreshToken or None
- `revoke(token_id)` → None

### ⬜ Step 8 — `core/security.py`
Two responsibilities:
- Password hashing: `hash_password(plain)` → str, `verify_password(plain, hashed)` → bool (using passlib/bcrypt)
- JWT: `create_access_token(user_id)`, `create_refresh_token()`, `decode_access_token(token)` → payload (using python-jose)

### ⬜ Step 9 — `services/auth_service.py`
Business logic only — calls repos and security, never touches DB directly.
- `signup(email, password)` → TokenResponse
- `login(email, password)` → TokenResponse
- `refresh(refresh_token)` → TokenResponse (with token rotation)
- `logout(refresh_token)` → None (revokes token in DB)

### ⬜ Step 10 — `api/v1/routes/auth.py`
Thin HTTP layer — parse request, call service, return response. No logic here.
- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

### ⬜ Step 11 — `main.py`
Wire everything together:
- Create `FastAPI()` app instance
- Register the auth router with prefix `/api/v1`
- Add centralized exception handlers (`core/exceptions.py`)
- Add health check endpoint: `GET /health`
- App boots and `/docs` (Swagger UI) is accessible

---

## Key Concepts for This Week
| Concept | Summary |
|---|---|
| Why hash passwords? | One-way hash — even if DB is leaked, passwords can't be reversed |
| Why bcrypt? | Deliberately slow — brute-force attacks take too long to be feasible |
| Access token (JWT) | Short-lived (15 min), stateless, no DB lookup needed to verify |
| Refresh token | Long-lived (30 days), stored hashed in DB, used only to get new access token |
| Token rotation | Each refresh issues a new refresh token and revokes the old one |
| Repository pattern | All DB queries in one place — services don't know SQL exists |
| Why async SQLAlchemy? | FastAPI is async; blocking DB calls would block the entire event loop |

---

## Decisions Made So Far
- Layer-first architecture (not domain-first) — learn patterns clearly first
- Refresh tokens stored hashed in DB (industry standard, not plaintext)
- Token rotation on every refresh (security best practice)
- UUID primary keys (not integer — harder to enumerate/guess)
- Async SQLAlchemy throughout (not sync — consistent with FastAPI's async nature)
