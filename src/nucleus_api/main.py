from fastapi import FastAPI
from nucleus_api.api.v1.routes.auth import router as auth_router

app = FastAPI(title="Nucleus API", version="0.1.0")

app.include_router(auth_router, prefix="/api/v1")

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}

