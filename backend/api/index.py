import sys
import os

# Add the parent directory to sys.path so we can import from main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangum import Mangum
from main import app

# Create the handler for Vercel
handler = Mangum(app, lifespan="off")

# For Vercel, we need to expose the handler as the default export
def handler_wrapper(event, context):
    return handler(event, context)

# This is what Vercel will call
app = handler_wrapper