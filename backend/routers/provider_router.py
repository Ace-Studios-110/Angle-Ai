from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from services.provider_service import get_provider_recommendations, generate_provider_table
from middlewares.auth import verify_auth_token
import json

router = APIRouter()

@router.get("/sessions/{session_id}/providers/{task_id}")
async def get_providers_for_task(
    session_id: str,
    task_id: str,
    current_user: dict = Depends(verify_auth_token)
):
    """Get provider recommendations for a specific implementation task"""
    try:
        # Extract business context from session (you may need to implement this)
        business_context = {
            "industry": "general business",  # This should come from session data
            "location": "United States",     # This should come from session data
            "business_type": "startup"       # This should come from session data
        }
        
        providers = await get_provider_recommendations(
            task_id=task_id,
            industry=business_context["industry"],
            location=business_context["location"],
            business_context=business_context
        )
        
        return JSONResponse({
            "success": True,
            "data": providers
        })
        
    except Exception as e:
        print(f"Error getting providers: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider recommendations")

@router.post("/sessions/{session_id}/providers/generate")
async def generate_custom_provider_table(
    session_id: str,
    request: Request,
    current_user: dict = Depends(verify_auth_token)
):
    """Generate a custom provider table for a specific task"""
    try:
        body = await request.json()
        task_type = body.get("task_type")
        industry = body.get("industry", "general business")
        location = body.get("location", "United States")
        business_context = body.get("business_context", {})
        
        if not task_type:
            raise HTTPException(status_code=400, detail="task_type is required")
        
        providers = await generate_provider_table(
            task_type=task_type,
            industry=industry,
            location=location,
            business_context=business_context
        )
        
        return JSONResponse({
            "success": True,
            "data": {
                "task_type": task_type,
                "industry": industry,
                "location": location,
                "providers": providers,
                "generated_at": "2024-01-01T00:00:00"  # This should be current timestamp
            }
        })
        
    except Exception as e:
        print(f"Error generating provider table: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate provider table")

@router.get("/sessions/{session_id}/providers/categories")
async def get_provider_categories(
    session_id: str,
    current_user: dict = Depends(verify_auth_token)
):
    """Get available provider categories"""
    try:
        categories = {
            "legal_services": {
                "description": "Legal and compliance services",
                "subcategories": ["business_formation", "contracts", "intellectual_property", "regulatory_compliance"]
            },
            "financial_services": {
                "description": "Financial and accounting services",
                "subcategories": ["banking", "accounting", "tax_preparation", "bookkeeping", "financial_planning"]
            },
            "marketing_services": {
                "description": "Marketing and advertising services", 
                "subcategories": ["digital_marketing", "branding", "content_creation", "social_media", "seo"]
            },
            "operational_services": {
                "description": "Operations and logistics services",
                "subcategories": ["supply_chain", "fulfillment", "inventory_management", "equipment", "facilities"]
            },
            "technology_services": {
                "description": "Technology and software services",
                "subcategories": ["software_development", "web_development", "cloud_services", "cybersecurity", "analytics"]
            }
        }
        
        return JSONResponse({
            "success": True,
            "data": categories
        })
        
    except Exception as e:
        print(f"Error getting provider categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider categories")

