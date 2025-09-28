from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File
from typing import Dict, List, Any, Optional
from services.implementation_task_manager import ImplementationTaskManager
from services.specialized_agents_service import agents_manager
from services.rag_service import conduct_rag_research, validate_with_rag
from services.service_provider_tables_service import generate_provider_table, get_task_providers
from middlewares.auth import verify_auth_token
import json
import os
import uuid
from datetime import datetime

router = APIRouter(
    tags=["Implementation"],
    dependencies=[Depends(verify_auth_token)]
)

# Global instance
task_manager = ImplementationTaskManager()

@router.get("/sessions/{session_id}/implementation/tasks")
async def get_current_implementation_task(session_id: str, request: Request):
    """Get the current implementation task for a session"""
    
    user_id = request.state.user["id"]
    
    try:
        # Get session data (you'll need to implement this based on your session service)
        session_data = {
            "business_name": "Your Business",
            "industry": "Technology",
            "location": "San Francisco, CA",
            "business_type": "Startup"
        }
        
        # Get completed tasks (you'll need to implement this based on your session service)
        completed_tasks = []
        
        # Get next task
        task_result = await task_manager.get_next_implementation_task(session_data, completed_tasks)
        
        if task_result.get("status") == "completed":
            return {
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
        
        return {
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