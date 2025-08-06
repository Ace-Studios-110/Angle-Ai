from db.supabase import supabase

async def create_session(user_id: str, title: str):
    response = supabase \
        .from_("chat_sessions") \
        .insert({"user_id": user_id, "title": title}) \
        .execute()

    if response.data:
        return response.data[0]
    else:
        raise Exception("Failed to create session")

async def list_sessions(user_id: str):
    response = supabase.from_("chat_sessions").select("*").eq("user_id", user_id).order("updated_at", desc=True).execute()
    return response.data

async def get_session(session_id: str, user_id: str):
    response = supabase.from_("chat_sessions").select("*").eq("id", session_id).eq("user_id", user_id).single().execute()
    return response.data

async def patch_session(session_id: str, updates: dict):
    response = supabase.from_("chat_sessions").update(updates).eq("id", session_id).execute()
    return response.data[0]