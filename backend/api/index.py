# backend/api/index.py
# Vercel entrypoint for FastAPI (ASGI). Must export `app`.

# Ensure we can import ../main.py when this file runs from /backend/api
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # add ../ to sys.path

from main import app  # <-- your FastAPI() instance from backend/main.py
