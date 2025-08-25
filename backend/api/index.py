from main import app
from fastapi import fastAPI
from mangum import Mangum
# 
handler = Mangum(app)