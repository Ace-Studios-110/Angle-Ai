# Vercel entrypoint: must export `app`
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # add ../ to sys.path
from main import app  # FastAPI() from backend/main.py
