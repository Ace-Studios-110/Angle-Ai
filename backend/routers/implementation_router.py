from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File
from typing import Dict, List, Any, Optional
from services.implementation_task_manager import ImplementationTaskManager
from services.specialized_agents_service import agents_manager
from services.rag_service import conduct_rag_research, validate_with_rag
from services.service_provider_tables_service import generate_provider_table, get_task_providers
from services.session_service import get_session
from services.chat_service import fetch_chat_history
from middlewares.auth import verify_auth_token
import json
import os
import uuid
from datetime import datetime
import random

router = APIRouter(
    tags=["Implementation"],
    dependencies=[Depends(verify_auth_token)]
)

# Missing endpoints that are causing 404 errors
@router.get("/sessions/{session_id}/service-provider-preview")
async def get_service_provider_preview(session_id: str, request: Request):
    """Get service provider preview for implementation transition"""
    try:
        return {
            "success": True,
            "result": {
                "providers": [
                    {
                        "name": "Local Business Consultant",
                        "type": "Business Strategy",
                        "local": True,
                        "description": "Local business consultant for personalized guidance"
                    },
                    {
                        "name": "Legal Services Inc.",
                        "type": "Legal Services",
                        "local": True,
                        "description": "Local legal services for business formation"
                    },
                    {
                        "name": "Accounting Pro",
                        "type": "Accounting",
                        "local": True,
                        "description": "Local accounting services for business setup"
                    }
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/implementation-insights")
async def get_implementation_insights(session_id: str, request: Request):
    """Get implementation insights for the user"""
    try:
        return {
            "success": True,
            "result": {
                "insights": [
                    "Focus on legal formation first - it's the foundation of your business",
                    "Set up proper accounting systems early to avoid complications later",
                    "Build your network - connect with local business owners and mentors",
                    "Start with MVP - don't try to build everything at once"
                ],
                "tips": [
                    "Break large tasks into smaller, manageable steps",
                    "Set realistic timelines and celebrate small wins",
                    "Stay organized with task tracking and documentation",
                    "Don't hesitate to ask for help from experts"
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/motivational-quote")
async def get_motivational_quote(session_id: str, request: Request):
    """Get a motivational quote for the implementation journey"""
    import random
    
    quotes = [
        {
            "quote": "Success is not final, failure is not fatal: it is the courage to continue that counts.",
            "author": "Winston Churchill"
        },
        {
            "quote": "The way to get started is to quit talking and begin doing.",
            "author": "Walt Disney"
        },
        {
            "quote": "Don't be afraid to give up the good to go for the great.",
            "author": "John D. Rockefeller"
        },
        {
            "quote": "Innovation distinguishes between a leader and a follower.",
            "author": "Steve Jobs"
        },
        {
            "quote": "The future belongs to those who believe in the beauty of their dreams.",
            "author": "Eleanor Roosevelt"
        }
    ]
    
    try:
        selected_quote = random.choice(quotes)
        return {
            "success": True,
            "result": selected_quote
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Global instance
task_manager = ImplementationTaskManager()

# Cache for implementation tasks to prevent repeated processing
task_cache = {}
CACHE_TTL = 300  # 5 minutes cache

@router.get("/sessions/{session_id}/implementation/tasks")
async def get_current_implementation_task(session_id: str, request: Request):
    """Get the current implementation task for a session"""
    
    user_id = request.state.user["id"]
    
    try:
        # Check cache first to prevent repeated processing
        cache_key = f"{session_id}_{user_id}"
        if cache_key in task_cache:
            cached_result = task_cache[cache_key]
            if (datetime.now() - cached_result['timestamp']).seconds < CACHE_TTL:
                print(f"📋 Using cached implementation task for session: {session_id}")
                return cached_result['data']
        
        # Fetch real session data from database
        session = await get_session(session_id, user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Extract business context from session data (if available)
        session_data = {
            "business_name": session.get("business_name"),
            "industry": session.get("industry"),
            "location": session.get("location"),
            "business_type": session.get("business_type")
        }
        
        # If session data doesn't have business context, extract from chat history
        if not session_data.get("business_name") or not session_data.get("industry"):
            print(f"📊 Session data missing business context - extracting from chat history")
            history = await fetch_chat_history(session_id)
            
            # Simple extraction from chat history
            for msg in history:
                if msg.get('role') == 'user':
                    content = msg.get('content', '')
                    content_lower = content.lower()
                    
                    # Extract domain business name
                    if ('.com' in content or '.net' in content or '.org' in content) and len(content) < 100:
                        session_data["business_name"] = content.strip()
                    
                    # Extract location (common city names)
                    cities = ['karachi', 'lahore', 'islamabad', 'san francisco', 'new york', 'london', 'dubai']
                    for city in cities:
                        if city in content_lower:
                            session_data["location"] = city.title()
                            break
                    
                    # Extract business structure
                    structures = ['llc', 'corporation', 'partnership', 'private limited']
                    for structure in structures:
                        if structure in content_lower:
                            session_data["business_type"] = structure.upper()
                            break
                    
                    # Extract industry
                    industries = {'beverage': ['beverage', 'drink', 'coke', 'soda'], 
                                'food': ['food', 'restaurant', 'cafe'],
                                'technology': ['tech', 'software', 'app', 'platform'],
                                'retail': ['retail', 'store', 'shop', 'marketplace']}
                    for industry, keywords in industries.items():
                        if any(keyword in content_lower for keyword in keywords):
                            session_data["industry"] = industry.title()
                            break
        
        # Apply defaults if still missing
        session_data["business_name"] = session_data.get("business_name") or "Your Business"
        session_data["industry"] = session_data.get("industry") or "General Business"
        session_data["location"] = session_data.get("location") or "United States"
        session_data["business_type"] = session_data.get("business_type") or "Startup"
        
        print(f"📊 Implementation task - final business context: {session_data}")
        
        # Get completed tasks (you'll need to implement this based on your session service)
        completed_tasks = []
        
        # Get next task
        task_result = await task_manager.get_next_implementation_task(session_data, completed_tasks)
        
        if task_result.get("status") == "completed":
            response_data = {
                "success": True,
                "message": "All implementation tasks completed",
                "current_task": None,
                "progress": {
                    "completed": 25,
                    "total": 25,
                    "percent": 100,
                    "phases_completed": 5
                }
            }
        else:
            response_data = {
                "success": True,
                "message": "Current implementation task retrieved",
                "current_task": {
                    "id": task_result["task_id"],
                    "title": task_result["task_details"].get("title", "Implementation Task"),
                    "description": task_result["task_details"].get("description", ""),
                    "purpose": task_result["task_details"].get("purpose", ""),
                    "options": task_result["task_details"].get("options", []),
                    "angel_actions": task_result["angel_actions"],
                    "estimated_time": task_result["estimated_time"],
                    "priority": task_result["priority"],
                    "phase_name": task_result["phase"],
                    "business_context": session_data
                },
                "progress": {
                    "completed": len(completed_tasks),
                    "total": 25,
                    "percent": int((len(completed_tasks) / 25) * 100),
                    "phases_completed": 0
                }
            }
        
        # Cache the response
        task_cache[cache_key] = {
            'data': response_data,
            'timestamp': datetime.now()
        }
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get implementation task: {str(e)}")

@router.post("/sessions/{session_id}/implementation/tasks/{task_id}/complete")
async def complete_implementation_task(
    session_id: str,
    task_id: str,
    request: Request,
    completion_data: Dict[str, Any]
):
    """Mark an implementation task as completed"""
    
    user_id = request.state.user["id"]
    
    try:
        # Get session data
        session_data = {
            "business_name": "Your Business",
            "industry": "Technology",
            "location": "San Francisco, CA",
            "business_type": "Startup"
        }
        
        # Validate completion using RAG
        validation_result = await validate_with_rag(
            json.dumps(completion_data),
            session_data,
            f"implementation_task_{task_id}"
        )
        
        # Generate completion feedback
        feedback_prompt = f"""
        Provide feedback on task completion for: {task_id}
        
        Task Completion Data: {completion_data}
        Validation Results: {validation_result.get('validation_results', '')}
        Business Context: {session_data}
        
        Provide feedback including:
        1. Completion Assessment: How well the task was completed
        2. Missing Elements: What might be missing
        3. Recommendations: Suggestions for improvement
        4. Next Steps: What to do next
        5. Success Indicators: Signs of successful completion
        
        Format as constructive feedback to help the user succeed.
        """
        
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": feedback_prompt}],
            temperature=0.3,
            max_tokens=1500
        )
        
        feedback = response.choices[0].message.content
        
        # Update progress (you'll need to implement this based on your session service)
        updated_progress = {
            "completed": 1,  # Increment based on your logic
            "total": 25,
            "percent": 4,  # Calculate based on your logic
            "phases_completed": 0
        }
        
        return {
            "success": True,
            "message": "Task completed successfully",
            "feedback": feedback,
            "validation_results": validation_result,
            "progress": updated_progress
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete task: {str(e)}")

@router.post("/sessions/{session_id}/implementation/help")
async def get_implementation_help(
    session_id: str,
    request: Request,
    help_request: Dict[str, Any]
):
    """Get help content for implementation task"""
    
    user_id = request.state.user["id"]
    task_id = help_request.get("task_id")
    help_type = help_request.get("help_type", "detailed")
    
    if not task_id:
        raise HTTPException(status_code=400, detail="Task ID is required")
    
    try:
        # Get session data
        session_data = {
            "business_name": "Your Business",
            "industry": "Technology",
            "location": "San Francisco, CA",
            "business_type": "Startup"
        }
        
        # Get guidance from specialized agents
        agent_guidance = await agents_manager.get_multi_agent_guidance(
            f"Provide detailed help and guidance for implementation task: {task_id}",
            session_data,
            []
        )
        
        # Conduct RAG research for additional context
        research_query = f"help guidance {task_id} {session_data.get('industry', '')} implementation"
        rag_research = await conduct_rag_research(research_query, session_data, "standard")
        
        # Generate comprehensive help content
        help_prompt = f"""
        Generate comprehensive help content for implementation task: {task_id}
        
        Business Context: {session_data}
        Agent Guidance: {agent_guidance}
        RAG Research: {rag_research.get('analysis', '')}
        
        Provide detailed help including:
        1. Task Overview: What this task involves
        2. Step-by-Step Guide: Detailed instructions
        3. Common Challenges: What to watch out for
        4. Best Practices: Recommended approaches
        5. Resources: Additional resources and tools
        6. FAQ: Common questions and answers
        
        Format as clear, actionable guidance that helps the user succeed.
        """
        
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": help_prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        
        help_content = response.choices[0].message.content
        
        return {
            "success": True,
            "message": "Help content generated successfully",
            "help_content": help_content,
            "agent_guidance": agent_guidance,
            "rag_research": rag_research
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get help content: {str(e)}")

@router.post("/sessions/{session_id}/implementation/tasks/{task_id}/kickstart")
async def get_implementation_kickstart(session_id: str, task_id: str, request: Request):
    """Get kickstart plan for implementation task"""
    
    user_id = request.state.user["id"]
    
    try:
        # Get session data
        session_data = {
            "business_name": "Your Business",
            "industry": "Technology",
            "location": "San Francisco, CA",
            "business_type": "Startup"
        }
        
        # Get task-specific providers
        providers = await get_task_providers(task_id, f"implementation task {task_id}", session_data)
        
        # Generate kickstart plan using agents
        kickstart_guidance = await agents_manager.get_multi_agent_guidance(
            f"Create a detailed kickstart plan for implementation task: {task_id}",
            session_data,
            []
        )
        
        # Generate sub-steps with Angel actions
        kickstart_prompt = f"""
        Create a detailed kickstart plan for implementation task: {task_id}
        
        Business Context: {session_data}
        Agent Guidance: {kickstart_guidance}
        
        Generate a comprehensive kickstart plan including:
        1. Overview: What this kickstart plan will accomplish
        2. Sub-steps: Detailed breakdown of actions
        3. Angel Actions: Specific actions Angel can perform for each sub-step
        4. Timeline: Estimated timeline for completion
        5. Resources: Required resources and tools
        6. Success Metrics: How to measure progress
        
        For each sub-step, specify what Angel can do:
        - Draft documents
        - Research requirements
        - Create templates
        - Connect with providers
        - Analyze options
        
        Format as structured plan with clear action items.
        """
        
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": kickstart_prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        
        kickstart_plan = response.choices[0].message.content
        
        return {
            "success": True,
            "message": "Kickstart plan generated successfully",
            "kickstart_plan": {
                "task_id": task_id,
                "plan": kickstart_plan,
                "service_providers": providers.get('provider_table', {}),
                "agent_guidance": kickstart_guidance,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get kickstart plan: {str(e)}")

@router.post("/sessions/{session_id}/implementation/contact")
async def get_implementation_service_providers(
    session_id: str,
    request: Request,
    contact_request: Dict[str, Any]
):
    """Get service providers for implementation task"""
    
    user_id = request.state.user["id"]
    task_id = contact_request.get("task_id")
    
    if not task_id:
        raise HTTPException(status_code=400, detail="Task ID is required")
    
    try:
        # Get session data
        session_data = {
            "business_name": "Your Business",
            "industry": "Technology",
            "location": "San Francisco, CA",
            "business_type": "Startup"
        }
        
        # Get service providers for the task
        provider_table = await generate_provider_table(
            f"implementation task {task_id}",
            session_data,
            session_data.get('location')
        )
        
        # Extract and format providers
        service_providers = []
        for category, category_data in provider_table.get('provider_tables', {}).items():
            if category_data.get('providers'):
                for provider in category_data['providers']:
                    service_providers.append({
                        **provider,
                        "category": category,
                        "task_relevance": "High" if task_id in provider.get('specialties', '').lower() else "Medium"
                    })
        
        # Sort by relevance and local preference
        service_providers.sort(key=lambda x: (x['task_relevance'], x['local']), reverse=True)
        
        return {
            "success": True,
            "message": "Service providers retrieved successfully",
            "service_providers": service_providers[:10],  # Return top 10 providers
            "provider_table": provider_table
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service providers: {str(e)}")

@router.post("/sessions/{session_id}/implementation/tasks/{task_id}/complete")
async def complete_implementation_task(
    session_id: str,
    task_id: str,
    request: Request,
    payload: Dict[str, Any]
):
    """Mark implementation task as completed"""
    
    user_id = request.state.user["id"]
    
    try:
        # Extract completion data
        decision = payload.get("decision", "")
        actions = payload.get("actions", "")
        documents = payload.get("documents", "")
        notes = payload.get("notes", "")
        
        # Here you would typically save this to a database
        # For now, we'll just return success
        
        return {
            "success": True,
            "message": "Task completed successfully",
            "result": {
                "task_id": task_id,
                "completed_at": datetime.now().isoformat(),
                "decision": decision,
                "actions": actions,
                "documents": documents,
                "notes": notes
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete task: {str(e)}")

@router.post("/sessions/{session_id}/implementation/tasks/{task_id}/upload-document")
async def upload_implementation_document(
    session_id: str,
    task_id: str,
    request: Request,
    file: UploadFile = File(...)
):
    """Upload document for implementation task"""
    
    user_id = request.state.user["id"]
    
    # Validate file type
    allowed_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/jpeg', 'image/png']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Please upload a PDF, DOC, DOCX, JPEG, or PNG file.")
    
    # Validate file size (max 10MB)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB.")
    
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
        
        return {
            "success": True,
            "message": "Document uploaded successfully",
            "filename": file.filename,
            "file_id": unique_filename,
            "task_id": task_id,
            "uploaded_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@router.get("/sessions/{session_id}/implementation/progress")
async def get_implementation_progress(session_id: str, request: Request):
    """Get implementation progress for a session"""
    
    user_id = request.state.user["id"]
    
    try:
        # Get progress data (you'll need to implement this based on your session service)
        progress_data = {
            "completed_tasks": 5,
            "total_tasks": 25,
            "percent_complete": 20,
            "phases_completed": 1,
            "current_phase": "legal_formation",
            "next_task": "business_registration",
            "estimated_completion": "8-12 weeks"
        }
        
        return {
            "success": True,
            "message": "Implementation progress retrieved",
            "progress": progress_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get implementation progress: {str(e)}")