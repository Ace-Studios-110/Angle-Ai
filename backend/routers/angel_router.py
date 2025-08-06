from fastapi import APIRouter, Request
from schemas.angel_schemas import ChatRequestSchema, CreateSessionSchema
from services.session_service import create_session, list_sessions, get_session, patch_session
from services.chat_service import fetch_chat_history, save_chat_message, fetch_phase_chat_history
from services.generate_plan_service import generate_full_business_plan, generate_full_roadmap_plan
from services.angel_service import get_angel_reply
from utils.progress import parse_tag, TOTALS_BY_PHASE, smart_trim_history
from middlewares.auth import verify_auth_token
from fastapi import Depends
import re

router = APIRouter(
    tags=["Angel"],
    dependencies=[Depends(verify_auth_token)]
)

@router.post("/sessions")
async def post_session(request: Request, payload: CreateSessionSchema):
    user_id = request.state.user["id"]
    session = await create_session(user_id, payload.title)
    return {"success": True, "message": "Session created", "result": session}


@router.get("/sessions")
async def get_sessions(request: Request):
    user_id = request.state.user["id"]
    sessions = await list_sessions(user_id)
    return {"success": True, "message": "Chat sessions fetched", "result": sessions}

@router.get("/sessions/{session_id}/history")
async def chat_history(request: Request, session_id: str):

    history = await fetch_chat_history(session_id)
    return {"success": True, "message": "Chat history fetched", "data": history}

@router.post("/sessions/{session_id}/chat")
async def post_chat(session_id: str, request: Request, payload: ChatRequestSchema):
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    history = await fetch_chat_history(session_id)

    # Save user message
    await save_chat_message(session_id, user_id, "user", payload.content)

    # Get AI reply
    assistant_reply = await get_angel_reply({"role": "user", "content": payload.content}, history)

    # Save assistant reply
    await save_chat_message(session_id, user_id, "assistant", assistant_reply)

    # Tag handling
    last_tag = session.get("asked_q")
    tag = parse_tag(assistant_reply)

    print(last_tag, tag)

    if last_tag and tag and last_tag != tag:
        session["answered_count"] += 1

    if tag:
        session["asked_q"] = tag
        session["current_phase"] = tag.split(".")[0]

        if tag.startswith("BUSINESS_PLAN.") and int(tag.split(".")[1]) >= 9:
            session["asked_q"] = "ROADMAP.01"
            session["current_phase"] = "ROADMAP"

    # Update session in DB
    await patch_session(session_id, {
        "asked_q": session["asked_q"],
        "answered_count": session["answered_count"],
        "current_phase": session["current_phase"]
    })

    # Clean response
    display_reply = re.sub(r'Question \d+ of \d+ \(\d+%\):', '', assistant_reply, flags=re.IGNORECASE)
    display_reply = re.sub(r'\[\[Q:[A-Z_]+\.\d{2}]]', '', display_reply)

    total = TOTALS_BY_PHASE.get(session["current_phase"], 0)

    return {
        "success": True,
        "message": "Angel chat processed successfully",
        "result": {
            "reply": display_reply.strip(),
            "progress": {
                "phase": session["current_phase"],
                "answered": session["answered_count"],
                "total": total,
                "percent": round((session["answered_count"] / total) * 100) if total else 0
            },
            "session_id": session_id
        }
    }

@router.post("/sessions/{session_id}/generate-plan")
async def generate_business_plan(request: Request, session_id: str):
    history = await fetch_chat_history(session_id)
    history_trimmed = smart_trim_history(history)  
    result = await generate_full_business_plan(history_trimmed) 
    return {
        "success": True,
        "message": "Business plan generated successfully",
        "result": result,
    }

@router.get("/sessions/{session_id}/roadmap-plan")
async def generate_roadmap_plan(session_id: str, request: Request):
    history = await fetch_chat_history(session_id)
    history_trimmed = smart_trim_history(history)
    roadmap = await generate_full_roadmap_plan(history_trimmed)
    return {
        "success": True,
        "result": roadmap
    }

@router.get("/sessions/{session_id}/chat/history")
async def get_phase_chat_history(
    session_id: str,
    request: Request,
    phase: str,
    limit: int = 15,
    offset: int = 0
):
    user_id = request.state.user["id"]

    messages = await fetch_phase_chat_history(session_id, phase, offset, limit)

    return {
        "success": True,
        "result": messages,
        "has_more": len(messages) == limit
    }
