from fastapi import APIRouter, Request, Depends, UploadFile, File
from schemas.angel_schemas import ChatRequestSchema, CreateSessionSchema
from services.session_service import create_session, list_sessions, get_session, patch_session
from services.chat_service import fetch_chat_history, save_chat_message, fetch_phase_chat_history
from services.generate_plan_service import generate_full_business_plan, generate_full_roadmap_plan, generate_comprehensive_business_plan_summary, generate_implementation_insights, generate_service_provider_preview, generate_motivational_quote
from services.angel_service import get_angel_reply, handle_roadmap_generation, handle_roadmap_to_implementation_transition
from utils.progress import parse_tag, TOTALS_BY_PHASE, calculate_phase_progress, calculate_combined_progress, smart_trim_history
from middlewares.auth import verify_auth_token
from fastapi.middleware.cors import CORSMiddleware
import re
import os
import uuid
from datetime import datetime

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
    angel_response = await get_angel_reply({"role": "user", "content": payload.content}, history, session)
    
    # Handle new return format
    if isinstance(angel_response, dict):
        assistant_reply = angel_response["reply"]
        web_search_status = angel_response.get("web_search_status", {"is_searching": False, "query": None})
        immediate_response = angel_response.get("immediate_response", None)
        transition_phase = angel_response.get("transition_phase", None)
        business_plan_summary = angel_response.get("business_plan_summary", None)
        session_update = angel_response.get("patch_session", None)
        show_accept_modify = angel_response.get("show_accept_modify", False)
    else:
        # Backward compatibility
        assistant_reply = angel_response
        web_search_status = {"is_searching": False, "query": None}
        immediate_response = None
        transition_phase = None
        business_plan_summary = None
        session_update = None
        show_accept_modify = False

    # Save assistant reply
    await save_chat_message(session_id, user_id, "assistant", assistant_reply)

    # Handle session updates (e.g., from Accept responses)
    if session_update:
        session.update(session_update)
        await patch_session(session_id, session_update)

    # Handle transition phases
    if transition_phase == "KYC_TO_BUSINESS_PLAN":
        # Update session to transition phase
        session["current_phase"] = "BUSINESS_PLAN"
        await patch_session(session_id, {
            "current_phase": "BUSINESS_PLAN",
            "asked_q": "BUSINESS_PLAN.01",
            "answered_count": 0
        })
        
        # Return transition response
        return {
            "success": True,
            "message": "KYC completed - transition to business plan",
            "result": {
                "reply": assistant_reply,
                "progress": {
                    "phase": "BUSINESS_PLAN",
                    "answered": 0,
                    "total": 2,
                    "percent": 0
                },
                "web_search_status": web_search_status,
                "immediate_response": immediate_response,
                "transition_phase": transition_phase,
                "question_number": None  # No question number for transition messages
            }
        }
    
    if transition_phase == "PLAN_TO_ROADMAP":
        # Update session to transition phase
        session["current_phase"] = "PLAN_TO_ROADMAP_TRANSITION"
        # Store transition data in session memory (not database)
        session["transition_data"] = {
            "business_plan_summary": business_plan_summary,
            "transition_type": "PLAN_TO_ROADMAP"
        }
        await patch_session(session_id, {
            "current_phase": session["current_phase"]
        })
        
        # Return transition response without normal tag processing
        return {
            "success": True,
            "message": "Business plan completed - transition to roadmap",
            "result": {
                "reply": assistant_reply,
                "progress": {
                    "phase": "PLAN_TO_ROADMAP_TRANSITION",
                    "answered": 46,
                    "total": 46,
                    "percent": 100
                },
                "session_id": session_id,
                "web_search_status": web_search_status,
                "immediate_response": immediate_response,
                "transition_phase": transition_phase,
                "business_plan_summary": business_plan_summary,
                "transition_data": session["transition_data"]
            }
        }

    # Check if this is a command response that should not trigger tag processing
    # Also includes verification messages
    command_indicators = [
        "Here's a draft for you",
        "Here's a draft based on what you've shared",
        "Let's work through this together",
        "Here's a refined version of your thoughts",
        "I'll create additional content for you",
        "Verification:",
        "Here's what I've captured so far",
        "Does this look accurate",
        "Does this look correct"
    ]
    
    is_command_response = any(indicator in assistant_reply for indicator in command_indicators)
    
    if is_command_response:
        print(f"🔧 Command response detected - skipping tag processing to prevent question skipping")
        # Don't process tags for command responses - stay on current question
        tag = None
    else:
        # Tag handling - Only increment when moving to a genuinely new question
        last_tag = session.get("asked_q")
        tag = parse_tag(assistant_reply)

    print(f"🏷️ Tag Analysis:")
    print(f"  - Last tag: {session.get('asked_q')}")
    print(f"  - Current tag: {tag}")
    print(f"  - Is command response: {is_command_response}")
    print(f"  - Current answered_count: {session.get('answered_count', 0)}")
    print(f"  - Assistant reply preview: {assistant_reply[:100]}...")

    # Only increment answered_count when moving to a genuinely new tagged question
    # Follow-up questions or clarifications should NOT increment the count
    # Skip increment for command responses
    if not is_command_response and last_tag and tag and last_tag != tag:
        # Check if this is a genuine progression to next question
        # (not just a clarification or follow-up)
        last_phase, last_num = last_tag.split(".")
        current_phase, current_num = tag.split(".")
        
        print(f"🔄 Tag Comparison:")
        print(f"  - Last phase: {last_phase}, Last num: {last_num}")
        print(f"  - Current phase: {current_phase}, Current num: {current_num}")
        
        # Only increment if moving to next sequential question
        if (current_phase == last_phase and int(current_num) == int(last_num) + 1) or \
           (current_phase != last_phase and current_num == "01"):
            session["answered_count"] += 1
            print(f"✅ Incremented answered_count to {session['answered_count']}")
        else:
            print(f"❌ No increment - not a sequential question progression")
    elif not is_command_response and not last_tag and tag:
        # First question with a tag - this should increment
        session["answered_count"] += 1
        print(f"✅ First question with tag - incremented answered_count to {session['answered_count']}")
    elif not is_command_response and not tag:
        print(f"⚠️ No tag found in assistant reply")
        # Fallback: If no tag but we have a conversation, increment conservatively
        if len(history) > 0:
            # Only increment by 1 if we haven't incremented recently
            current_count = session.get("answered_count", 0)
            # Only increment if we have at least 2 messages (1 Q&A pair) and haven't incremented yet
            if len(history) >= 2 and current_count == 0:
                session["answered_count"] = 1
                print(f"🔄 Fallback: Incremented answered_count to 1 (first question without tag)")
            elif len(history) >= 4 and current_count == 1:
                session["answered_count"] = 2
                print(f"🔄 Fallback: Incremented answered_count to 2 (second question without tag)")
    else:
        if is_command_response:
            print(f"🔧 Command response - skipping answered_count increment")
        else:
            print(f"⚠️ No tag change or missing tags")

    if tag and not is_command_response:
        # Validate tag format and detect backwards progression
        previous_tag = session.get("asked_q", "")
        if previous_tag:
            try:
                prev_phase, prev_num = previous_tag.split(".")
                prev_num = int(prev_num)
                
                current_phase, current_num = tag.split(".")
                current_num = int(current_num)
                
                # Check if tag matches "Question X" in the message text
                question_num_match = re.search(r'Question\s+(\d+)(?:\s+of\s+\d+)?', assistant_reply)
                if question_num_match:
                    message_question_num = int(question_num_match.group(1))
                    if message_question_num != current_num:
                        print(f"⚠️ WARNING: Tag mismatch detected!")
                        print(f"  Message says: 'Question {message_question_num}'")
                        print(f"  Tag says: {tag} (question {current_num})")
                        print(f"  Using message question number as source of truth")
                        # Use the message question number
                        corrected_tag = f"{current_phase}.{message_question_num:02d}"
                        print(f"🔧 Correcting tag from {tag} to {corrected_tag}")
                        tag = corrected_tag
                        current_num = message_question_num
                
                # Check for backwards progression
                if prev_phase == current_phase and current_num < prev_num:
                    print(f"⚠️ WARNING: Backwards question progression detected!")
                    print(f"  Previous: {previous_tag} (question {prev_num})")
                    print(f"  Current: {tag} (question {current_num})")
                    print(f"  This may indicate an AI model error in tag generation")
                    
                    # Fix backwards progression by incrementing the question number
                    corrected_num = prev_num + 1
                    corrected_tag = f"{current_phase}.{corrected_num:02d}"
                    print(f"🔧 Correcting tag from {tag} to {corrected_tag}")
                    tag = corrected_tag
            except (ValueError, IndexError) as e:
                print(f"⚠️ Error parsing tag format: {e}")
        
        session["asked_q"] = tag
        session["current_phase"] = tag.split(".")[0]
        print(f"📝 Updated session: asked_q={tag}, current_phase={tag.split('.')[0]}")
        
        # Auto-transition to roadmap after business plan completion
        # Only transition when we've completed all business plan questions (46 total)
        if tag.startswith("BUSINESS_PLAN."):
            try:
                question_num = int(tag.split(".")[1])
                if question_num > 46:
                    session["asked_q"] = "ROADMAP.01"
                    session["current_phase"] = "ROADMAP"
                    print(f"🔄 Auto-transitioned to ROADMAP after completing BUSINESS_PLAN question {question_num}")
            except (ValueError, IndexError):
                print(f"⚠️ Error parsing question number from tag: {tag}")
                # Don't transition if we can't parse the question number
    else:
        # If no tag found or command response, try to maintain current phase or set default
        if not session.get("current_phase"):
            session["current_phase"] = "KYC"
            print(f"📝 Set default phase to KYC")
        
        if is_command_response:
            print(f"🔧 Command response - maintaining current session state without tag updates")

    # Calculate progress based on current phase and CURRENT TAG (not answered_count)
    # CRITICAL: Use asked_q as the source of truth for what question we're on
    current_phase = session["current_phase"]
    answered_count = session["answered_count"]
    current_tag = session.get("asked_q")
    
    print(f"📈 Progress Calculation Input:")
    print(f"  - current_phase: {current_phase}")
    print(f"  - answered_count: {answered_count}")
    print(f"  - current_tag (asked_q): {current_tag}")
    print(f"  - Parsed tag from reply: {tag}")
    print(f"  - session data: {session}")
    
    # Calculate phase-specific progress for phase indicator
    phase_progress = calculate_phase_progress(current_phase, answered_count, current_tag)
    print(f"📊 Phase Progress Output: {phase_progress}")
    
    # For KYC and Business Plan phases, also calculate combined progress (Overall Progress)
    if current_phase in ["KYC", "BUSINESS_PLAN"]:
        combined_progress = calculate_combined_progress(current_phase, answered_count, current_tag)
        print(f"📊 Combined Progress Output (for Overall Progress): {combined_progress}")
        # Add combined progress info to phase_progress for frontend
        phase_progress["overall_progress"] = {
            "answered": combined_progress["answered"],
            "total": combined_progress["total"],
            "percent": combined_progress["percent"]
        }
    
    print(f"📊 Final Progress Data Sent to Frontend: {phase_progress}")
    
    # Update session in DB (without phase_progress since it's calculated on the fly)
    await patch_session(session_id, {
        "asked_q": session["asked_q"],
        "answered_count": session["answered_count"],
        "current_phase": session["current_phase"]
    })

    # Extract question number from tag before removing it
    question_number = None
    if tag and "." in tag:
        try:
            question_number = int(tag.split(".")[1])
        except (ValueError, IndexError):
            question_number = None
    
    # Clean response
    display_reply = re.sub(r'Question \d+ of \d+ \(\d+%\):', '', assistant_reply, flags=re.IGNORECASE)
    display_reply = re.sub(r'\[\[Q:[A-Z_]+\.\d{2}]]', '', display_reply)
    
    # Clean up excessive spacing for Angel introduction text
    if 'welcome to founderport' in display_reply.lower():
        # Reduce excessive line breaks throughout the entire text
        display_reply = re.sub(r'\n{4,}', '\n\n', display_reply)  # Reduce 4+ newlines to 2
        display_reply = re.sub(r'\n{3}', '\n\n', display_reply)  # Reduce 3 newlines to 2
        # Fix spacing around journey question
        display_reply = re.sub(r'\n\s*\n\s*Are you ready to begin your journey\?\s*\n\s*\n', '\n\nAre you ready to begin your journey?\n\n', display_reply)
        # Fix spacing around questionnaire intro
        display_reply = re.sub(r'\n\s*\n\s*Let\'s start with the Getting to Know You questionnaire', '\n\nLet\'s start with the Getting to Know You questionnaire', display_reply)
        # Final cleanup - ensure no more than 2 consecutive newlines anywhere
        display_reply = re.sub(r'\n{3,}', '\n\n', display_reply)

    # Return progress information
    progress_info = phase_progress

    return {
        "success": True,
        "message": "Angel chat processed successfully",
        "result": {
            "reply": display_reply.strip(),
            "progress": progress_info,
            "session_id": session_id,
            "web_search_status": web_search_status,
            "immediate_response": immediate_response,
            "show_accept_modify": show_accept_modify,
            "question_number": question_number
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

async def patch_session_context_from_response(session_id, response_content, tag, session):
    """Extract and store key information from user responses"""
    
    # Skip extraction if this is a command word (Accept, Modify, Draft, etc.)
    command_words = ["accept", "modify", "draft", "support", "scrapping", "scraping", "draft more", "ok", "okay", "yes", "no"]
    response_lower = response_content.strip().lower()
    
    if response_lower in command_words:
        print(f"🔧 Skipping session context extraction for command word: {response_content}")
        return
    
    # Skip if response is too long (likely from Support/Draft commands)
    if len(response_content) > 500:
        print(f"🔧 Skipping session context extraction for long response ({len(response_content)} chars)")
        return
    
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
        print(f"📝 Extracting session context: {list(updates.keys())}")
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
        
        # Extract the reply content from the response object
        improved_reply = improved_response.get("reply", improved_response) if isinstance(improved_response, dict) else improved_response
        
        return {
            "success": True,
            "message": "Here's your modified response",
            "result": {
                "improved_response": improved_reply,
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
    
    # Extract the reply content from the response object
    question_reply = question_response.get("reply", question_response) if isinstance(question_response, dict) else question_response
    
    return {
        "success": True,
        "message": "Navigated to previous question",
        "result": {
            "question": clean_reply_for_display(question_reply),
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

# TOTALS_BY_PHASE is now defined in utils/progress.py

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

@router.get("/sessions/{session_id}/business-plan-summary")
async def get_business_plan_summary(request: Request, session_id: str):
    """Generate comprehensive business plan summary for Plan to Roadmap Transition"""
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    history = await fetch_chat_history(session_id)
    history_trimmed = smart_trim_history(history)
    
    try:
        result = await generate_comprehensive_business_plan_summary(history_trimmed)
        return {
            "success": True,
            "message": "Business plan summary generated successfully",
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error generating business plan summary: {str(e)}"
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

@router.get("/sessions/{session_id}/enhanced-roadmap")
async def generate_enhanced_roadmap(session_id: str, request: Request):
    """Generate enhanced roadmap with comprehensive summary, execution advice, and motivational elements"""
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    history = await fetch_chat_history(session_id)
    history_trimmed = smart_trim_history(history)
    
    try:
        # Generate the enhanced roadmap with all new features
        roadmap_result = await generate_full_roadmap_plan(history_trimmed)
        
        # Add additional metadata for the enhanced UI
        enhanced_result = {
            **roadmap_result,
            "enhanced_features": {
                "research_foundation": True,
                "planning_champion_award": True,
                "execution_advice": True,
                "motivational_elements": True,
                "comprehensive_summary": True,
                "success_statistics": True
            },
            "ui_metadata": {
                "show_research_banner": True,
                "show_achievement_section": True,
                "show_execution_excellence": True,
                "show_success_stats": True,
                "enhanced_action_button": True
            }
        }
        
        return {
            "success": True,
            "message": "Enhanced roadmap generated successfully with comprehensive features",
            "result": enhanced_result
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error generating enhanced roadmap: {str(e)}"
        }

@router.post("/sessions/{session_id}/modify-roadmap")
async def modify_roadmap(session_id: str, request: Request):
    """Modify the roadmap content with user edits"""
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    try:
        payload = await request.json()
        modified_content = payload.get("modified_content", "")
        
        if not modified_content:
            return {
                "success": False,
                "message": "No modified content provided"
            }
        
        # Store the modified roadmap in the session
        session["modified_roadmap"] = modified_content
        session["roadmap_modified_at"] = datetime.now().isoformat()
        await patch_session(session_id, session)
        
        return {
            "success": True,
            "message": "Roadmap modified successfully",
            "modified_at": session["roadmap_modified_at"]
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error modifying roadmap: {str(e)}"
        }

@router.get("/sessions/{session_id}/implementation-insights")
async def get_implementation_insights(session_id: str, request: Request):
    """Generate RAG-powered implementation insights for the transition phase"""
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    try:
        # Extract business context from session
        business_context = session.get("business_context", {})
        industry = business_context.get("industry", "")
        location = business_context.get("location", "")
        business_type = business_context.get("business_type", "")
        
        # Generate implementation insights using RAG
        insights = await generate_implementation_insights(industry, location, business_type)
        
        return {
            "success": True,
            "insights": insights
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error generating implementation insights: {str(e)}"
        }

@router.get("/sessions/{session_id}/service-provider-preview")
async def get_service_provider_preview(session_id: str, request: Request):
    """Generate RAG-powered service provider preview for the transition phase"""
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    try:
        # Extract business context from session
        business_context = session.get("business_context", {})
        industry = business_context.get("industry", "")
        location = business_context.get("location", "")
        business_type = business_context.get("business_type", "")
        
        # Generate service provider preview using RAG
        providers = await generate_service_provider_preview(industry, location, business_type)
        
        return {
            "success": True,
            "providers": providers
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error generating service provider preview: {str(e)}"
        }

@router.get("/sessions/{session_id}/motivational-quote")
async def get_motivational_quote(session_id: str, request: Request):
    """Get a motivational quote for the transition phase"""
    try:
        # Generate or retrieve a motivational quote
        quote = await generate_motivational_quote()
        
        return {
            "success": True,
            "quote": quote
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error generating motivational quote: {str(e)}"
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

@router.post("/sessions/{session_id}/transition-decision")
async def handle_transition_decision(session_id: str, request: Request, payload: dict):
    """Handle Approve/Revisit decisions for Plan to Roadmap transition"""
    
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    decision = payload.get("decision")  # "approve" or "revisit"
    
    if decision == "approve":
        # Transition to Roadmap phase
        session["current_phase"] = "ROADMAP"
        session["asked_q"] = "ROADMAP.01"
        session["answered_count"] = 0
        
        await patch_session(session_id, {
            "current_phase": session["current_phase"],
            "asked_q": session["asked_q"],
            "answered_count": session["answered_count"]
        })
        
        # Generate roadmap
        history = await fetch_chat_history(session_id)
        roadmap_response = await handle_roadmap_generation(session, history)
        
        return {
            "success": True,
            "message": "Plan approved - transitioning to roadmap",
            "result": {
                "action": "transition_to_roadmap",
                "roadmap": roadmap_response["roadmap_content"],
                "progress": {
                    "phase": "ROADMAP",
                    "answered": 0,
                    "total": 1,
                    "percent": 0
                },
                "transition_phase": roadmap_response["transition_phase"]
            }
        }
    
    elif decision == "revisit":
        # Return to Business Plan phase for modifications
        session["current_phase"] = "BUSINESS_PLAN"
        # Keep the current progress instead of resetting to 01
        # This allows user to continue from where they left off
        current_asked_q = session.get("asked_q", "BUSINESS_PLAN.46")
        if not current_asked_q.startswith("BUSINESS_PLAN."):
            current_asked_q = "BUSINESS_PLAN.46"
        
        # Calculate correct answered count from the tag
        answered_from_tag = 46  # Default to 46 if at end
        if current_asked_q and "." in current_asked_q:
            try:
                answered_from_tag = int(current_asked_q.split(".")[1])
            except (ValueError, IndexError):
                answered_from_tag = 46
        
        # Sync answered_count with the tag to fix any discrepancies
        session["answered_count"] = answered_from_tag
        
        await patch_session(session_id, {
            "current_phase": session["current_phase"],
            "asked_q": current_asked_q,
            "answered_count": answered_from_tag  # Sync this!
        })
        
        return {
            "success": True,
            "message": "Plan review mode activated",
            "result": {
                "action": "revisit_plan",
                "progress": {
                    "phase": "BUSINESS_PLAN",
                    "answered": answered_from_tag,  # Use tag-based calculation
                    "total": 46,
                    "percent": 100
                }
            }
        }
    
    else:
        return {
            "success": False,
            "message": "Invalid decision. Please choose 'approve' or 'revisit'"
        }

@router.post("/sessions/{session_id}/revisit-plan-with-areas")
async def revisit_plan_with_areas(session_id: str, request: Request, payload: dict):
    """Handle revisit with specific modification areas"""
    
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    modification_areas = payload.get("modification_areas", [])
    
    if not modification_areas:
        return {
            "success": False,
            "message": "No modification areas specified"
        }
    
    # Store modification areas in session for guidance
    session["modification_areas"] = modification_areas
    session["current_phase"] = "BUSINESS_PLAN"
    
    # Map modification areas to specific business plan sections
    area_to_section_mapping = {
        "business-overview": "BUSINESS_PLAN.01-05",
        "market-research": "BUSINESS_PLAN.06-12", 
        "financial-projections": "BUSINESS_PLAN.13-20",
        "operations": "BUSINESS_PLAN.21-28",
        "marketing-strategy": "BUSINESS_PLAN.29-35",
        "legal-compliance": "BUSINESS_PLAN.36-42"
    }
    
    # Determine starting point based on modification areas
    starting_sections = [area_to_section_mapping.get(area) for area in modification_areas if area in area_to_section_mapping]
    
    # Start from the earliest section that needs modification
    if starting_sections:
        earliest_section = min(starting_sections, key=lambda x: int(x.split('.')[1].split('-')[0]))
        session["asked_q"] = f"BUSINESS_PLAN.{earliest_section.split('.')[1].split('-')[0].zfill(2)}"
    else:
        session["asked_q"] = "BUSINESS_PLAN.01"
    
    await patch_session(session_id, {
        "current_phase": session["current_phase"],
        "asked_q": session["asked_q"],
        "modification_areas": modification_areas
    })
    
    # Generate guidance message for modifications
    modification_guidance = f"""Based on your selection, I'll guide you through modifying the following areas of your business plan:

{', '.join([area.replace('-', ' ').replace('_', ' ').title() for area in modification_areas])}

Let's start with the first area that needs attention. I'll provide specific guidance and questions to help you refine each section."""
    
    # Save guidance message to chat
    await save_chat_message(session_id, user_id, "assistant", modification_guidance)
    
    return {
        "success": True,
        "message": "Plan modification mode activated",
        "result": {
            "action": "revisit_plan_with_areas",
            "modification_areas": modification_areas,
            "guidance": modification_guidance,
            "progress": {
                "phase": "BUSINESS_PLAN",
                "answered": session.get("answered_count", 0),
                "total": 46,
                "percent": 0
            }
        }
        }

@router.post("/sessions/{session_id}/start-implementation")
async def start_implementation(session_id: str, request: Request):
    """Handle transition from Roadmap to Implementation phase"""
    
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    # Transition to Implementation phase
    session["current_phase"] = "IMPLEMENTATION"
    session["asked_q"] = "IMPLEMENTATION.01"
    session["answered_count"] = 0
    
    await patch_session(session_id, {
        "current_phase": session["current_phase"],
        "asked_q": session["asked_q"],
        "answered_count": session["answered_count"]
    })
    
    # Get the first implementation task
    from services.implementation_service import get_next_implementation_task
    first_task = await get_next_implementation_task(session, [])
    
    # Generate implementation transition message and first question
    implementation_prompt = "The user has approved their roadmap and wants to start the implementation phase. Please provide a motivational transition message and present the first implementation task/question."
    
    session_context = {
        "current_phase": "IMPLEMENTATION",
        "industry": session.get("industry"),
        "location": session.get("location")
    }
    
    implementation_response = await get_angel_reply(
        {"role": "user", "content": implementation_prompt},
        [],  # Empty history for implementation start
        session_context
    )
    
    # Extract the reply content from the response object
    reply_content = implementation_response.get("reply", implementation_response) if isinstance(implementation_response, dict) else implementation_response
    
    # Save the implementation transition message
    await save_chat_message(session_id, user_id, "assistant", reply_content)
    
    return {
        "success": True,
        "message": "Implementation phase started successfully",
        "result": {
            "action": "start_implementation",
            "reply": reply_content,
            "progress": {
                "phase": "IMPLEMENTATION",
                "answered": 0,
                "total": 10,
                "percent": 0
            },
            "first_task": first_task
        }
    }

@router.post("/sessions/{session_id}/roadmap-to-implementation-transition")
async def roadmap_to_implementation_transition(session_id: str, request: Request):
    """Handle transition from Roadmap to Implementation phase"""
    
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    # Generate transition message
    history = await fetch_chat_history(session_id)
    transition_response = await handle_roadmap_to_implementation_transition(session, history)
    
    return {
        "success": True,
        "message": "Roadmap to Implementation transition prepared",
        "result": {
            "action": "roadmap_to_implementation_transition",
            "reply": transition_response["reply"],
            "progress": {
                "phase": "ROADMAP_TO_IMPLEMENTATION_TRANSITION",
                "answered": 1,
                "total": 1,
                "percent": 100
            },
            "transition_phase": transition_response["transition_phase"]
        }
    }

@router.post("/sessions/{session_id}/upload-business-plan")
async def upload_business_plan(
    session_id: str,
    request: Request,
    file: UploadFile = File(...)
):
    """Upload and process a business plan document"""
    user_id = request.state.user["id"]
    
    # Validate file type
    allowed_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if file.content_type not in allowed_types:
        return {
            "success": False,
            "error": "Please upload a PDF, DOC, or DOCX file."
        }
    
    # Validate file size (max 10MB)
    if file.size > 10 * 1024 * 1024:
        return {
            "success": False,
            "error": "File size must be less than 10MB."
        }
    
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'pdf'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create a chat message about the uploaded document
        upload_message = f"📄 **Business Plan Document Uploaded**\n\n**File:** {file.filename}\n**Size:** {file.size} bytes\n**Type:** {file.content_type}\n**Uploaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nI've received your business plan document. I can help you:\n\n• **Analyze** the content and provide feedback\n• **Extract** key information for our business planning process\n• **Compare** it with our questionnaire responses\n• **Suggest** improvements or missing sections\n\nWould you like me to analyze this document and integrate it into our business planning process?"
        
        # Save the upload message to chat history
        await save_chat_message(session_id, "assistant", upload_message)
        
        return {
            "success": True,
            "message": "Business plan uploaded successfully",
            "filename": file.filename,
            "file_id": unique_filename,
            "chat_message": upload_message
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to upload file: {str(e)}"
        }
