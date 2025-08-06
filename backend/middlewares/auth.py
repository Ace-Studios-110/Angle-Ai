from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os, jwt

oauth_scheme = HTTPBearer()
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

async def verify_auth_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(oauth_scheme)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
        request.state.user = {"id": payload["sub"], "email": payload["email"]}
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        print(f"❌ Token is invalid: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

