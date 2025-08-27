
# logging.basicConfig(level=logging.DEBUG)
import os
from fastapi import FastAPI, Request, Response
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

app = FastAPI(title="Founderport Angel Assistant")

# ✅ CORS Support
# Enhanced CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],  # or list explicit headers you send (Authorization, Content-Type, etc.)
)
# Manual OPTIONS handler for problematic preflight requests
@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "86400"
    return response

# ✅ Root route for health check
@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Founderport Angel Assistant API is running",
        "version": "1.0.0"
    }

# ✅ Routers
app.include_router(auth_router, prefix="/auth")
app.include_router(angel_router, prefix="/angel")

# ✅ Global Exception Handlers
app.add_exception_handler(AuthApiError, supabase_auth_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)