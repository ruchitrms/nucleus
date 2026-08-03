# Week 2 Build Plan: Error Handling, Authenticated Routes, Products

## Context
Project: Nucleus — e-commerce backend (FastAPI + PostgreSQL + Redis)
Week 2 start: August 4, 2026
Building on: Full auth system (signup, login, refresh, logout) + 49 tests — all passing.

---

## Where We Left Off
Auth is complete and tested. One gap from Week 1–2 remains:
- ⬜ Centralized error handling — currently raw 500s leak stack traces to the client (security issue)

After that, we move into the Products domain and Redis caching (Week 3–4 of the project plan).

---

## What You Will Build This Week

```
src/nucleus_api/
├── core/
│   └── exceptions.py        ← Step 1: custom exception classes + FastAPI handlers
├── api/v1/routes/
│   ├── auth.py              ← Step 2: add get_current_user dependency (reuse in every future route)
│   └── users.py             ← Step 2: GET /me — first authenticated endpoint
├── models/
│   └── product.py           ← Step 3: Product ORM model
├── schemas/
│   └── product.py           ← Step 4: product request/response shapes
├── repositories/
│   └── product_repo.py      ← Step 5: product DB queries
├── services/
│   └── product_service.py   ← Step 6: product business logic
└── api/v1/routes/
    └── products.py          ← Step 7: product HTTP endpoints
```

Plus:
- Alembic migration for the products table (between Steps 3 and 4)
- HTTP-level tests using `httpx.AsyncClient` (Step 8)

---

## Build Order

### ⬜ Step 1 — `core/exceptions.py`: Centralized Error Handling
**Why first:** Currently if something crashes, FastAPI returns a raw 500 with a Python stack trace.
Clients (mobile apps, frontends) should never see internal error details — it's both a bad UX and a security leak.

**What to build:**
- Custom exception classes (e.g. `NotFoundException`, `ConflictException`)
- FastAPI exception handlers registered in `main.py`
- A consistent error response shape: `{"error": "...", "detail": "..."}`

**Learning goal:** Understand the difference between HTTP exceptions (expected, e.g. 404) vs unhandled exceptions (unexpected, e.g. crash). Both need to be handled gracefully.

---

### ⬜ Step 2 — `get_current_user` dependency + `GET /api/v1/users/me`
**Why:** Every protected route needs a way to know *who* is making the request.
This is FastAPI's dependency injection system at its best.

**What to build:**
- `get_current_user(token: str = Depends(oauth2_scheme)) -> User` in `core/dependencies.py`
  - Decodes the JWT from the `Authorization: Bearer <token>` header
  - Looks up the user by the `sub` field
  - Raises 401 if token is missing, invalid, or user not found
- `GET /api/v1/users/me` → returns the logged-in user's profile (UserResponse)

**Learning goal:** Understand FastAPI's `Depends()` system — how dependencies chain together and how the same dependency can protect multiple routes with zero code repetition.

---

### ⬜ Step 3 — `models/product.py`
**What to build:**
- `Product(Base)` ORM model with columns:
  - `id` (UUID, primary key)
  - `name` (str, indexed)
  - `description` (str, nullable)
  - `price` (Numeric — not Float, reasons below)
  - `stock` (int, default 0)
  - `is_active` (bool, default True)
  - `created_at`, `updated_at` (timestamps)

**Learning goal:** Why `Numeric` (fixed-precision) instead of `Float` for money?
Float is binary approximation — `0.1 + 0.2 = 0.30000000000000004`. Prices stored as floats will have rounding errors. Always use `Decimal`/`Numeric` for money.

---

### ⬜ Step 3b — Alembic migration for products
```bash
alembic revision --autogenerate -m "create products table"
alembic upgrade head
```
Verify the table exists in the DB before moving on.

---

### ⬜ Step 4 — `schemas/product.py`
**What to build:**
- `ProductCreate`: name, description, price, stock (input)
- `ProductUpdate`: all fields optional (for PATCH — partial updates)
- `ProductResponse`: all fields including id, is_active, created_at (output)

**Learning goal:** The difference between `POST` (full create) and `PATCH` (partial update) — why PATCH fields are all `Optional`.

---

### ⬜ Step 5 — `repositories/product_repo.py`
**What to build:**
- `get_all(skip, limit)` — paginated product listing
- `get_by_id(product_id)` → Product or None
- `create(name, description, price, stock)` → Product
- `update(product_id, **fields)` → Product
- `delete(product_id)` → None (soft delete: set `is_active = False`, don't actually delete rows)

**Learning goal:** Why soft delete? Audit trails, order history integrity — if you hard-delete a product, old orders lose their reference.

---

### ⬜ Step 6 — `services/product_service.py`
**What to build:**
- `list_products(skip, limit)` → list[ProductResponse]
- `get_product(product_id)` → ProductResponse (raises 404 if not found)
- `create_product(data)` → ProductResponse (admin only — enforce in route, not service)
- `update_product(product_id, data)` → ProductResponse
- `delete_product(product_id)` → None

**Learning goal:** The service decides *what* to do (raise 404 if not found). The route decides *how to respond* (404 HTTP status). These are different concerns.

---

### ⬜ Step 7 — `api/v1/routes/products.py`
**What to build:**
- `GET /api/v1/products` — public, paginated (no auth required)
- `GET /api/v1/products/{id}` — public
- `POST /api/v1/products` — protected (requires `get_current_user`)
- `PATCH /api/v1/products/{id}` — protected
- `DELETE /api/v1/products/{id}` — protected

**Learning goal:** Some routes are public, some are protected. FastAPI's `Depends()` lets you apply `get_current_user` per-route or per-router — understand the difference.

---

### ⬜ Step 8 — HTTP-Level Tests (`tests/integration/test_auth_routes.py`)
**What to build:**
- Use `httpx.AsyncClient(app=app, base_url="http://test")` — no running server needed
- Test the full HTTP request → response cycle for auth:
  - `POST /signup` → 200 + tokens
  - `POST /signup` same email again → 400
  - `POST /login` correct credentials → 200 + tokens
  - `POST /login` wrong password → 401
  - `GET /me` with valid token → 200 + user data
  - `GET /me` without token → 401
  - `GET /me` with expired/invalid token → 401

**Learning goal:** This layer tests what your unit and repo integration tests can't — HTTP status codes, response shapes, and header handling. It catches things like "the route returns 200 but the response body has the wrong fields".

---

## Key Concepts for This Week

| Concept | Summary |
|---|---|
| Centralized error handling | One place handles all errors → consistent responses, no stack traces leaked |
| FastAPI `Depends()` | Dependency injection — declare what a route needs, FastAPI provides it |
| `get_current_user` | The JWT gateway — every protected route uses this as a dependency |
| `Numeric` vs `Float` | Use `Numeric`/`Decimal` for money — float has binary rounding errors |
| Soft delete | Mark `is_active = False` instead of deleting — preserves audit trail |
| Pagination | `skip` + `limit` — don't return 10,000 products in one response |
| HTTP-level tests | Test what actually goes over the wire — status codes, response shapes, headers |

---

## Decisions to Make This Week
- **Who can create/update/delete products?** For now: any authenticated user.
  Later you'll add an `is_superuser` flag and proper role-based access control.
- **Pagination style:** `skip`/`limit` (simplest) vs cursor-based (scalable for large datasets).
  Use `skip`/`limit` for now — understand why cursor pagination exists before you need it.

---

## Completed Steps
*(mark ✅ as you finish each one)*
