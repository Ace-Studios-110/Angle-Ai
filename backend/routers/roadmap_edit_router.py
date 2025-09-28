from fastapi import APIRouter, Request, HTTPException
from typing import Dict
from datetime import datetime
from services.angel_service import client, ANGEL_SYSTEM_PROMPT
from services.session_service import get_session
from services.chat_service import save_chat_message

router = APIRouter()

@router.post("/sessions/{session_id}/regenerate-roadmap-section")
async def regenerate_roadmap_section(session_id: str, request: Request, payload: Dict):
    """Regenerate a specific section of the roadmap"""
    
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    section_id = payload.get("section_id")
    section_title = payload.get("section_title")
    current_content = payload.get("current_content")
    
    if not all([section_id, section_title, current_content]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    try:
        # Generate regeneration prompt
        regeneration_prompt = f"""
        Regenerate the roadmap section: "{section_title}"
        
        Current content:
        {current_content}
        
        Business context:
        - Business Name: {session.get('business_name', 'Your Business')}
        - Industry: {session.get('industry', 'general business')}
        - Location: {session.get('location', 'United States')}
        - Business Type: {session.get('business_type', 'startup')}
        
        Please regenerate this section with:
        1. More detailed and actionable steps
        2. Specific timelines and deadlines
        3. Clear task ownership (Angel vs User)
        4. Industry-specific considerations
        5. Local resources and requirements
        6. Success metrics and milestones
        
        Make it comprehensive, actionable, and tailored to their specific business context.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": ANGEL_SYSTEM_PROMPT},
                {"role": "user", "content": regeneration_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        regenerated_content = response.choices[0].message.content
        
        # Save regeneration message to chat
        regeneration_message = f"🔄 **Section Regenerated: {section_title}**\n\n{regenerated_content}"
        await save_chat_message(session_id, "assistant", regeneration_message)
        
        return {
            "success": True,
            "regenerated_content": regenerated_content,
            "section_id": section_id,
            "section_title": section_title
        }
        
    except Exception as e:
        print(f"Error regenerating roadmap section: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to regenerate section: {str(e)}")

@router.post("/sessions/{session_id}/update-roadmap")
async def update_roadmap(session_id: str, request: Request, payload: Dict):
    """Update the entire roadmap with edited content"""
    
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    updated_content = payload.get("updated_content")
    
    if not updated_content:
        raise HTTPException(status_code=400, detail="Missing updated content")
    
    try:
        # Save updated roadmap to session
        from services.session_service import patch_session
        await patch_session(session_id, {
            "roadmap_content": updated_content,
            "roadmap_modified": True,
            "roadmap_last_modified": datetime.now().isoformat()
        })
        
        # Save update message to chat
        update_message = f"📝 **Roadmap Updated**\n\nYour roadmap has been successfully updated with your customizations. The changes have been saved and will be reflected in your implementation phase."
        await save_chat_message(session_id, "assistant", update_message)
        
        return {
            "success": True,
            "message": "Roadmap updated successfully",
            "updated_content": updated_content
        }
        
    except Exception as e:
        print(f"Error updating roadmap: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update roadmap: {str(e)}")

@router.get("/sessions/{session_id}/roadmap-history")
async def get_roadmap_history(session_id: str, request: Request):
    """Get roadmap modification history"""
    
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    try:
        # Get roadmap history from session
        roadmap_history = session.get("roadmap_history", [])
        
        return {
            "success": True,
            "history": roadmap_history,
            "current_version": session.get("roadmap_content", ""),
            "last_modified": session.get("roadmap_last_modified"),
            "is_modified": session.get("roadmap_modified", False)
        }
        
    except Exception as e:
        print(f"Error getting roadmap history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get roadmap history: {str(e)}")

@router.post("/sessions/{session_id}/revert-roadmap")
async def revert_roadmap(session_id: str, request: Request, payload: Dict):
    """Revert roadmap to a previous version"""
    
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    version_id = payload.get("version_id")
    
    if not version_id:
        raise HTTPException(status_code=400, detail="Missing version ID")
    
    try:
        # Get roadmap history
        roadmap_history = session.get("roadmap_history", [])
        
        # Find the version to revert to
        target_version = None
        for version in roadmap_history:
            if version.get("id") == version_id:
                target_version = version
                break
        
        if not target_version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        # Revert to the target version
        from services.session_service import patch_session
        await patch_session(session_id, {
            "roadmap_content": target_version["content"],
            "roadmap_modified": True,
            "roadmap_last_modified": datetime.now().isoformat()
        })
        
        # Save revert message to chat
        revert_message = f"↩️ **Roadmap Reverted**\n\nYour roadmap has been reverted to version from {target_version.get('timestamp', 'unknown date')}."
        await save_chat_message(session_id, "assistant", revert_message)
        
        return {
            "success": True,
            "message": "Roadmap reverted successfully",
            "reverted_content": target_version["content"]
        }
        
    except Exception as e:
        print(f"Error reverting roadmap: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to revert roadmap: {str(e)}")
