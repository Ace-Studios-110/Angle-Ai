import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from gotrue.errors import AuthApiError

# Routers
from routers.auth_router import auth_router
from routers.angel_router import router as angel_router

# Middlewares
from middlewares.auth import verify_auth_token

# Exceptions
from exceptions import (
    global_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    supabase_auth_exception_handler,
)

app = FastAPI(
    title="Founderport Angel Assistant",
    description="Angel Assistant API",
    version="1.0.0"
)

# ✅ CORS Configuration - More permissive for debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://angle-ai.vercel.app",
        "https://*.vercel.app",  # Allow all vercel subdomains
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ✅ Root route for health check
@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Founderport Angel Assistant API is running",
        "version": "1.0.0"
    }

# ✅ Debug endpoint to check CORS
@app.get("/debug")
async def debug(request: Request):
    return {
        "origin": request.headers.get("origin"),
        "host": request.headers.get("host"),
        "user_agent": request.headers.get("user-agent"),
        "all_headers": dict(request.headers)
    }

# ✅ Routers
app.include_router(auth_router, prefix="/auth")
app.include_router(angel_router, prefix="/angel")

# ✅ Global Exception Handlers
app.add_exception_handler(AuthApiError, supabase_auth_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# For Vercel
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)