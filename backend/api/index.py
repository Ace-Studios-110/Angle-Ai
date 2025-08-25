import sys
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Verify critical environment variables before importing
    if not os.getenv("SUPABASE_URL"):
        raise ValueError("SUPABASE_URL environment variable is required")
    if not os.getenv("SUPABASE_KEY"):
        raise ValueError("SUPABASE_KEY environment variable is required")
    
    from main import app as fastapi_app
    from mangum import Mangum
    
    # Create Mangum handler
    handler = Mangum(fastapi_app, lifespan="off")
    
    # Export for Vercel
    app = handler
    
except Exception as e:
    print(f"Error during initialization: {e}")
    # Create a simple error app
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    error_app = FastAPI()
    
    @error_app.get("/")
    async def error_handler():
        return JSONResponse(
            status_code=500,
            content={"error": f"Initialization failed: {str(e)}"}
        )
    
    @error_app.get("/{path:path}")
    async def catch_all(path: str):
        return JSONResponse(
            status_code=500,
            content={"error": f"Initialization failed: {str(e)}"}
        )
    
    from mangum import Mangum
    app = Mangum(error_app, lifespan="off")