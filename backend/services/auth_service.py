from db.supabase import supabase

async def create_user(email: str, password: str):
    response = supabase.auth.sign_up({"email": email, "password": password})
    if response.user is None:
        raise Exception("User not created")
    return response.user

async def authenticate_user(email: str, password: str):
    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if response.session is None:
        raise Exception("Invalid credentials")
    return response.session

async def send_reset_password_email(email: str):
    supabase.auth.reset_password_for_email(email)
    return {"email": email}

def refresh_session(refresh_token: str):
    response = supabase.auth.refresh_session(refresh_token)
    if response.session is None:
        raise Exception("Token refresh failed")
    return response.session