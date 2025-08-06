from db.supabase import supabase

async def fetch_chat_history(session_id: str):
    response = supabase.from_("chat_history").select("role, content").eq("session_id", session_id).order("created_at").execute()
    return response.data

async def save_chat_message(session_id: str, user_id: str, role: str, content: str):
    supabase.from_("chat_history").insert({"session_id": session_id, "user_id": user_id, "role": role, "content": content}).execute()

async def fetch_phase_chat_history(session_id: str, phase: str, offset: int = 0, limit: int = 15):
    response = (
        supabase
        .table("chat_history")
        .select("role, content, phase, created_at")
        .eq("session_id", session_id)
        .eq("phase", phase)
        .order("created_at", desc=False)
        .range(offset, offset + limit - 1)
        .execute()
    )

    if response.error:
        raise Exception(f"Supabase error: {response.error.message}")

    return response.data

