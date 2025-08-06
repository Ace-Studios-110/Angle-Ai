from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST
from pydantic import ValidationError
from gotrue.errors import AuthApiError  
import traceback

async def global_exception_handler(request: Request, exc: Exception):
    print("⚠️ Global Exception Caught")
    print(f"🔗 Path: {request.url.path}")
    print(f"🧵 Exception Type: {type(exc).__name__}")
    print(f"📝 Exception Message: {str(exc)}")
    traceback.print_exc()
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": str(exc),
        },
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    print("🚨 HTTPException Caught")
    print(f"🔗 Path: {request.url.path}")
    print(f"📦 Status Code: {exc.status_code}")
    print(f"📝 Detail: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": "HTTP Exception",
            "message": exc.detail,
        },
    )

async def validation_exception_handler(request: Request, exc: ValidationError):
    print("📛 Validation Error Caught")
    print(f"🔗 Path: {request.url.path}")
    print(f"📝 Errors: {exc.errors()}")

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation Error",
            "details": exc.errors(),
        },
    )

async def supabase_auth_exception_handler(request: Request, exc: AuthApiError):
    print("🔐 Supabase Auth Error Caught")
    print(f"🔗 Path: {request.url.path}")
    print(f"📝 Error Message: {exc.message}")
    
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": "Authentication Failed",
            "message": exc.message,
        },
    )
