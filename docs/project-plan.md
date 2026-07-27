# Nucleus — E-Commerce Backend: Full Project Plan

## Project Overview
A production-oriented e-commerce backend API built as a **learning project** across Phase 1 of a backend engineering curriculum. The goal is not just to make it work, but to **understand every decision made**.

**Approach: Learning-first, not vibe coding.**
Every file is written by hand with full understanding of what it does and why. No auto-generated code, no copy-paste without understanding. Each step is discussed conceptually before implementation. The bar is: can you explain every decision out loud?

**Stack:**
- Language: Python 3.11
- Framework: FastAPI
- Database: PostgreSQL 16 (via Docker)
- ORM: SQLAlchemy (async)
- Migrations: Alembic
- Cache: Redis
- Background jobs: Celery
- Auth: JWT (access + refresh tokens) + passlib/bcrypt
- Validation: Pydantic v2
- Testing: pytest + pytest-asyncio
- Linting/formatting: ruff, mypy

**Domain:** Users, Products, Cart, Orders (payments mocked)

**Architecture:** Layer-first monolith (routes → services → repositories → models). Intentionally not microservices for Phase 1 — understand the monolith deeply before splitting.

---

## Folder Structure (Layer-First)
```
src/nucleus_api/
├── main.py                         ← FastAPI app entry point
├── api/v1/routes/                  ← HTTP handlers only, no business logic
│   ├── auth.py
│   ├── users.py
│   ├── products.py
│   ├── cart.py
│   └── orders.py
├── core/                           ← Cross-cutting concerns
│   ├── config.py                   ← Env vars via pydantic-settings ✅
│   ├── security.py                 ← JWT + password hashing
│   ├── exceptions.py               ← Custom exception classes
│   └── middleware.py               ← Logging, request ID
├── db/
│   ├── base.py                     ← SQLAlchemy declarative base
│   └── session.py                  ← Async engine + session factory
├── models/                         ← SQLAlchemy ORM (DB tables)
│   ├── user.py
│   ├── product.py
│   ├── order.py
│   └── cart.py
├── schemas/                        ← Pydantic request/response shapes
│   ├── user.py
│   ├── product.py
│   ├── order.py
│   └── cart.py
├── repositories/                   ← All DB queries, nowhere else
│   ├── user_repo.py
│   ├── product_repo.py
│   ├── order_repo.py
│   └── cart_repo.py
├── services/                       ← Business logic
│   ├── auth_service.py
│   ├── product_service.py
│   ├── order_service.py
│   └── cart_service.py
└── workers/                        ← Celery background tasks
    ├── email_tasks.py
    └── order_tasks.py
```

---

## Phase 1 Weekly Plan

### Week 1–2: Auth, Validation, Error Handling
Build the user authentication system end-to-end.

**Deliverables:**
- User signup/login with bcrypt-hashed passwords
- JWT access token (15 min) + refresh token (30 days) with rotation
- Refresh tokens stored hashed in DB, revoked on logout
- Input validation on every endpoint via Pydantic schemas
- Centralized error handling — no scattered try/catch
- API versioning at `/api/v1/...`
- `main.py` wired up and app boots cleanly

**Checkpoint:** Can you explain out loud why plaintext passwords are dangerous and how JWT expiry/refresh works?

---

### Week 3–4: Caching + Queues
Add Redis caching and async background job processing.

**Deliverables:**
- Products/listings cached in Redis (TTL-based)
- Cache invalidation on product update/delete
- Celery worker with Redis as broker
- One async task: welcome email on signup (mocked, logs to stdout)
- Understand: what happens if the Celery worker crashes mid-job?

**Checkpoint:** Can you explain TTL vs event-based cache invalidation and why async processing reduces user-facing latency?

---

### Week 5: Docker + Deployment
Containerize the full stack and deploy to a real environment.

**Deliverables:**
- `Dockerfile` for the FastAPI app
- `docker-compose.yml` extended with app + Redis (DB already added in Week 1)
- Structured logging (JSON logs, not `print()`)
- Health-check endpoint: `GET /health`
- Deployed to Render / Railway / Fly.io (free tier)
- UptimeRobot or equivalent monitoring on the health endpoint

**Checkpoint:** If the app crashed right now, would you know within 5 minutes?

---

### Week 6–7: Tests + Documentation + Refactor
Write tests for critical paths, clean up fast-and-dirty code, write the README.

**Deliverables:**
- Unit tests for auth service (signup, login, refresh, logout)
- Integration tests for auth endpoints
- Refactor anything written quickly in weeks 1–4
- README: architecture overview, how to run locally, decisions and why
- Consider whether to restructure to domain-first before Phase 2

**Checkpoint:** Could a stranger clone this repo and run it in under 10 minutes using only your README?

---

### Week 8: Buffer
Catch-up week. Use it to finish anything that slipped. If ahead, skim System Design material for Phase 2.

---

## Key Decisions Made
| Decision | Choice | Reason |
|---|---|---|
| Language | Python 3.11 | Stable, widely supported by all ecosystem libs |
| Framework | FastAPI | Async-native, Pydantic built-in, industry adoption |
| ORM | SQLAlchemy async | Industry standard, async support, pairs with Alembic |
| Auth | JWT + refresh tokens | Stateless access tokens, revocable refresh tokens |
| Architecture | Layer-first monolith | Learn patterns clearly before microservices |
| DB versioning | Alembic | Only mature migration tool for SQLAlchemy |
| Background jobs | Celery + Redis | Industry standard, pairs with Redis already in stack |

---

## Environment Setup
- Python 3.11 virtual environment at `.venv/`
- Dependencies: `requirements/base.txt` (prod) + `requirements/dev.txt` (dev/test)
- Environment variables: copy `.env.example` → `.env` and fill in values
- Start database: `docker compose up -d` (from project root)
- Activate venv: `source .venv/bin/activate`
