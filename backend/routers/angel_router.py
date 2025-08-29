from fastapi import APIRouter, Request, Depends
from schemas.angel_schemas import ChatRequestSchema, CreateSessionSchema
from services.session_service import create_session, list_sessions, get_session, patch_session
from services.chat_service import fetch_chat_history, save_chat_message, fetch_phase_chat_history
from services.generate_plan_service import generate_full_business_plan, generate_full_roadmap_plan
from services.angel_service import get_angel_reply
from utils.progress import parse_tag, TOTALS_BY_PHASE, smart_trim_history
from middlewares.auth import verify_auth_token
from fastapi.middleware.cors import CORSMiddleware
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

def clean_reply_for_display(reply):
    """Clean reply by removing progress indicators and tags"""
    # Remove progress indicators
    reply = re.sub(r'Question \d+ of \d+ \(\d+%\):', '', reply, flags=re.IGNORECASE)
    
    # Remove machine tags
    reply = re.sub(r'\[\[Q:[A-Z_]+\.\d{2}]]\s*', '', reply)
    
    # Remove extra whitespace
    reply = re.sub(r'\n\s*\n', '\n\n', reply)
    
    return reply.strip()

def get_phase_display_name(phase):
    """Get user-friendly phase names"""
    phase_names = {
        "KYC": "Getting to Know You",
        "BUSINESS_PLAN": "Business Planning", 
        "ROADMAP": "Creating Your Roadmap",
        "IMPLEMENTATION": "Implementation & Launch"
    }
    return phase_names.get(phase, phase)

async def update_session_context_from_response(session_id, response_content, tag, session):
    """Extract and store key information from user responses"""
    
    # Extract key information based on KYC question
    updates = {}
    
    if tag == "KYC.01":  # Name
        updates["user_name"] = response_content.strip()
    elif tag == "KYC.04":  # Work situation  
        updates["employment_status"] = response_content.strip()
    elif tag == "KYC.05":  # Business idea
        updates["has_business_idea"] = "yes" in response_content.lower()
        if updates["has_business_idea"]:
            updates["business_idea_brief"] = response_content.strip()
    elif tag == "KYC.08":  # Business type
        updates["business_type"] = response_content.strip()
    elif tag == "KYC.09":  # Motivation
        updates["motivation"] = response_content.strip()
    elif tag == "KYC.10":  # Location
        updates["location"] = response_content.strip()
    elif tag == "KYC.11":  # Industry
        updates["industry"] = response_content.strip()
    elif tag == "KYC.07":  # Skills comfort level
        updates["skills_assessment"] = response_content.strip()
        
    # Update session with extracted information
    if updates:
        await patch_session(session_id, updates)
        session.update(updates)

@router.post("/sessions/{session_id}/command")
async def handle_command(session_id: str, request: Request, payload: dict):
    """Handle Accept/Modify commands for Draft and Scrapping responses"""
    
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    command = payload.get("command")  # "accept" or "modify"
    draft_content = payload.get("draft_content")
    modification_feedback = payload.get("feedback", "")

    if command == "accept":
        # Save the draft as the user's answer
        await save_chat_message(session_id, user_id, "user", draft_content)
        
        # Move to next question
        current_tag = session.get("asked_q")
        if current_tag:
            # Increment question number
            phase, num = current_tag.split(".")
            next_num = str(int(num) + 1).zfill(2)
            next_tag = f"{phase}.{next_num}"
            
            session["asked_q"] = next_tag
            session["answered_count"] += 1
            
            await patch_session(session_id, {
                "asked_q": session["asked_q"],
                "answered_count": session["answered_count"]
            })
        
        return {
            "success": True,
            "message": "Answer accepted, moving to next question",
            "action": "next_question"
        }
    
    elif command == "modify":
        # Process modification request
        history = await fetch_chat_history(session_id)
        
        modify_prompt = f"The user wants to modify this response based on their feedback:\n\nOriginal: {draft_content}\n\nFeedback: {modification_feedback}\n\nPlease provide an improved version."
        
        session_context = {
            "current_phase": session.get("current_phase", "KYC"),
            "industry": session.get("industry"),
            "location": session.get("location")
        }
        
        improved_response = await get_angel_reply(
            {"role": "user", "content": modify_prompt},
            history,
            session_context
        )
        
        return {
            "success": True,
            "message": "Here's your modified response",
            "result": {
                "improved_response": improved_response,
                "show_accept_modify": True
            }
        }

@router.get("/sessions/{session_id}/artifacts/{artifact_type}")
async def get_artifact(session_id: str, artifact_type: str, request: Request):
    """Retrieve generated artifacts like business plans and roadmaps"""
    
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    try:
        artifact = await fetch_artifact(session_id, artifact_type)
        if not artifact:
            return {"success": False, "message": "Artifact not found"}
            
        return {
            "success": True,
            "result": {
                "content": artifact["content"],
                "created_at": artifact["created_at"],
                "type": artifact_type
            }
        }
    except Exception as e:
        return {"success": False, "message": f"Error retrieving artifact: {str(e)}"}

@router.post("/sessions/{session_id}/navigate")
async def navigate_to_question(session_id: str, request: Request, payload: dict):
    """Allow navigation back to previous questions for modifications"""
    
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    target_tag = payload.get("target_tag")  # e.g., "KYC.05"
    
    if not target_tag:
        return {"success": False, "message": "Target question tag required"}
    
    # Validate target tag format
    if not re.match(r'^(KYC|BUSINESS_PLAN|ROADMAP|IMPLEMENTATION)\.\d{2}$', target_tag):
        return {"success": False, "message": "Invalid question tag format"}
    
    # Update session to target question
    session["asked_q"] = target_tag
    session["current_phase"] = target_tag.split(".")[0]
    
    await patch_session(session_id, {
        "asked_q": session["asked_q"],
        "current_phase": session["current_phase"]
    })
    
    # Get the question text for the target tag
    history = await fetch_chat_history(session_id)
    
    # Generate response for the target question
    navigation_prompt = f"The user wants to revisit and potentially modify their answer to question {target_tag}. Please re-present this question and their previous answer if available."
    
    session_context = {
        "current_phase": session["current_phase"],
        "industry": session.get("industry"),
        "location": session.get("location")
    }
    
    question_response = await get_angel_reply(
        {"role": "user", "content": navigation_prompt},
        history,
        session_context
    )
    
    return {
        "success": True,
        "message": "Navigated to previous question",
        "result": {
            "question": clean_reply_for_display(question_response),
            "current_tag": target_tag,
            "phase": session["current_phase"]
        }
    }

# Database helper functions for artifacts and enhanced session management

async def save_artifact(session_id: str, artifact_type: str, content: str):
    """Save generated artifacts to database"""
    # Implementation depends on your database structure
    # This is a placeholder for the database operation
    pass

async def fetch_artifact(session_id: str, artifact_type: str):
    """Fetch artifact from database"""
    # Implementation depends on your database structure
    # This is a placeholder for the database operation
    pass

# Updated TOTALS_BY_PHASE to reflect correct question counts
TOTALS_BY_PHASE = {
    "KYC": 20,
    "BUSINESS_PLAN": 46,  # Updated based on full questionnaire
    "ROADMAP": 1,
    "IMPLEMENTATION": 10  # Estimated based on typical implementation tasks
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
