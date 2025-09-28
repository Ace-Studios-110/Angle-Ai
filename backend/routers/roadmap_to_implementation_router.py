from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from services.roadmap_to_implementation_service import (
    prepare_implementation_transition,
    get_motivational_quote,
    get_service_provider_preview,
    generate_implementation_insights
)
from middlewares.auth import verify_auth_token
import json

router = APIRouter()

@router.post("/sessions/{session_id}/roadmap-to-implementation-transition")
async def create_roadmap_to_implementation_transition(
    session_id: str,
    request: Request,
    current_user: dict = Depends(verify_auth_token)
):
    """Create comprehensive roadmap to implementation transition"""
    try:
        # Get session data from request body or session storage
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
        
        # Extract session data (this would typically come from your session storage)
        session_data = {
            "business_name": body.get("business_name", "Your Business"),
            "industry": body.get("industry", "general business"),
            "location": body.get("location", "United States"),
            "business_type": body.get("business_type", "startup")
        }
        
        # Get roadmap content (this would typically come from your roadmap storage)
        roadmap_content = body.get("roadmap_content", "Roadmap content not available")
        
        # Prepare the transition
        transition_data = await prepare_implementation_transition(session_data, roadmap_content)
        
        if not transition_data["success"]:
            raise HTTPException(status_code=500, detail=transition_data.get("error", "Failed to prepare transition"))
        
        return JSONResponse(content={
            "success": True,
            "message": "Implementation transition prepared successfully",
            "result": {
                "transition_phase": "ROADMAP_TO_IMPLEMENTATION_TRANSITION",
                "motivational_quote": transition_data["motivational_quote"],
                "service_providers": transition_data["service_providers"],
                "implementation_insights": transition_data["implementation_insights"],
                "business_context": transition_data["business_context"],
                "reply": f"🚀 **Roadmap to Implementation Transition** 🚀\n\nCongratulations! You've successfully completed your comprehensive business plan and detailed launch roadmap for \"{session_data['business_name']}\". Now it's time to transition from planning into execution mode.\n\n**\"{transition_data['motivational_quote']['quote']}\"** – {transition_data['motivational_quote']['author']}\n\n---\n\n## 🎯 **Time to Transition from Planning to Action**\n\nYou've built a solid foundation with your business plan and roadmap. The time has come to transition from planning into execution mode. This is where your entrepreneurial journey truly begins to take shape.\n\n*This implementation process is tailored specifically to your \"{session_data['business_name']}\" business in the {session_data['industry']} industry, located in {session_data['location']}. Every recommendation is designed to help you build the business of your dreams.*"
            }
        })
        
    except Exception as e:
        print(f"Error in roadmap to implementation transition: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/service-provider-preview")
async def get_service_provider_preview_endpoint(
    session_id: str,
    current_user: dict = Depends(verify_auth_token)
):
    """Get service provider preview for implementation transition"""
    try:
        # This would typically get session data from your session storage
        # For now, we'll use default values
        business_context = {
            "business_name": "Your Business",
            "industry": "general business", 
            "location": "United States",
            "business_type": "startup"
        }
        
        providers = await get_service_provider_preview(business_context)
        
        return JSONResponse(content={
            "success": True,
            "providers": providers
        })
        
    except Exception as e:
        print(f"Error getting service provider preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/implementation-insights")
async def get_implementation_insights_endpoint(
    session_id: str,
    current_user: dict = Depends(verify_auth_token)
):
    """Get implementation insights for transition"""
    try:
        # This would typically get session data from your session storage
        business_context = {
            "business_name": "Your Business",
            "industry": "general business",
            "location": "United States", 
            "business_type": "startup"
        }
        
        insights = await generate_implementation_insights(business_context, "Roadmap content placeholder")
        
        return JSONResponse(content={
            "success": True,
            "insights": insights
        })
        
    except Exception as e:
        print(f"Error getting implementation insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/motivational-quote")
async def get_motivational_quote_endpoint(
    session_id: str,
    current_user: dict = Depends(verify_auth_token)
):
    """Get motivational quote for transition"""
    try:
        # This would typically get session data from your session storage
        business_context = {
            "business_name": "Your Business",
            "industry": "general business",
            "location": "United States",
            "business_type": "startup"
        }
        
        quote = await get_motivational_quote(business_context)
        
        return JSONResponse(content={
            "success": True,
            "quote": quote
        })
        
    except Exception as e:
        print(f"Error getting motivational quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/start-implementation")
async def start_implementation_phase(
    session_id: str,
    request: Request,
    current_user: dict = Depends(verify_auth_token)
):
    """Start the implementation phase"""
    try:
        # This would typically initialize the implementation phase
        # and return the first implementation task
        
        return JSONResponse(content={
            "success": True,
            "message": "Implementation phase started successfully",
            "result": {
                "progress": {
                    "phase": "IMPLEMENTATION",
                    "answered": 0,
                    "total": 10,
                    "percent": 0
                },
                "reply": "🚀 **Implementation Phase Started!** 🚀\n\nWelcome to the Implementation phase! I'll now guide you through executing each task step-by-step, turning your roadmap into actionable results.\n\n[[Q:IMPLEMENTATION.01]]\n\nLet's start with your first implementation task. Each task will be presented individually with detailed descriptions, multiple decision options, and all the support you need to succeed.\n\nReady to begin building your business? Let's start with the first task!"
            }
        })
        
    except Exception as e:
        print(f"Error starting implementation phase: {e}")
        raise HTTPException(status_code=500, detail=str(e))
