from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from nucleus_api.api.v1.routes.auth import router as auth_router
from nucleus_api.core.exceptions import NotFoundException, ConflictException, UnauthorizedException

app = FastAPI(title="Nucleus API", version="0.1.0")

app.include_router(auth_router, prefix="/api/v1")

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )   

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    ) 

@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": exc.detail},
    )   

@app.exception_handler(ConflictException)
async def conflict_exception_handler(request, exc): 
    return JSONResponse(
        status_code=409,
        content={"detail": exc.detail},
    )   

@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request, exc):  
    return JSONResponse(
        status_code=401,
        content={"detail": exc.detail},
    )

