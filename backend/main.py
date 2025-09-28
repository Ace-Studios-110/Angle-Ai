# import logging
# logging.basicConfig(level=logging.DEBUG)
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from gotrue.errors import AuthApiError

# Routers
from routers.auth_router import auth_router
from routers.angel_router import router as angel_router
from routers.implementation_router import router as implementation_router
from routers.roadmap_edit_router import router as roadmap_edit_router
from routers.roadmap_to_implementation_router import router as roadmap_to_implementation_router
from routers.provider_router import router as provider_router
from routers.specialized_agents_router import router as specialized_agents_router
from routers.implementation_router import router as implementation_router
from routers.appendices_router import router as appendices_router

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

# ✅ Root route for health check
@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Founderport Angel Assistant API is running",
        "version": "1.0.0"
    }

# ✅ CORS Support
origins = [
    "https://angle-ai-zsdt.vercel.app",
    "https://angle-ai.vercel.app",
    "http://localhost:3000",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ✅ Routers
app.include_router(auth_router, prefix="/auth")
app.include_router(angel_router, prefix="/angel")
app.include_router(implementation_router, prefix="/implementation")
app.include_router(roadmap_edit_router, prefix="/roadmap")
app.include_router(roadmap_to_implementation_router, prefix="/roadmap-to-implementation")
app.include_router(provider_router, prefix="/providers")
app.include_router(specialized_agents_router, prefix="/specialized-agents")
app.include_router(appendices_router, prefix="/appendices")

# ✅ Global Exception Handlers
app.add_exception_handler(AuthApiError, supabase_auth_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
