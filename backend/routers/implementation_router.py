from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from typing import List, Dict, Optional
import json
from services.implementation_service import (
    get_implementation_task,
    get_next_implementation_task,
    generate_task_guidance,
    generate_service_providers,
    generate_kickstart_plan,
    handle_task_completion,
    get_implementation_progress
)
from services.session_service import get_session, patch_session
from services.chat_service import save_chat_message, fetch_chat_history
from utils.progress import calculate_phase_progress

router = APIRouter()

@router.get("/sessions/{session_id}/implementation/tasks")
async def get_implementation_tasks(session_id: str, request: Request):
    """Get all implementation tasks for a session"""
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    if session["current_phase"] != "IMPLEMENTATION":
        raise HTTPException(status_code=400, detail="Session not in implementation phase")
    
    completed_tasks = session.get("completed_implementation_tasks", [])
    next_task = await get_next_implementation_task(session, completed_tasks)
    
    return {
        "success": True,
        "current_task": next_task,
        "completed_tasks": completed_tasks,
        "progress": get_implementation_progress(completed_tasks)
    }

@router.get("/sessions/{session_id}/implementation/tasks/{task_id}")
async def get_specific_task(session_id: str, task_id: str, request: Request):
    """Get a specific implementation task with guidance"""
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    task = await get_implementation_task(task_id, session)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Generate guidance and service providers
    guidance = await generate_task_guidance(task, session)
    service_providers = await generate_service_providers(task, session)
    
    return {
        "success": True,
        "task": task,
        "guidance": guidance,
        "service_providers": service_providers
    }

@router.post("/sessions/{session_id}/implementation/tasks/{task_id}/kickstart")
async def get_kickstart_plan(session_id: str, task_id: str, request: Request):
    """Generate kickstart plan for a specific task"""
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    task = await get_implementation_task(task_id, session)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    kickstart_plan = await generate_kickstart_plan(task, session)
    
    return {
        "success": True,
        "kickstart_plan": kickstart_plan
    }

@router.post("/sessions/{session_id}/implementation/tasks/{task_id}/complete")
async def complete_task(
    session_id: str, 
    task_id: str, 
    request: Request,
    completion_data: Dict
):
    """Mark a task as completed with verification"""
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    task = await get_implementation_task(task_id, session)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Handle task completion
    completion_result = await handle_task_completion(task_id, completion_data, session)
    
    # Update session with completed task
    completed_tasks = session.get("completed_implementation_tasks", [])
    if task_id not in completed_tasks:
        completed_tasks.append(task_id)
    
    await patch_session(session_id, {
        "completed_implementation_tasks": completed_tasks
    })
    
    # Save completion message to chat
    completion_message = f"✅ **Task Completed: {task['title']}**\n\n{completion_result['verification']}"
    await save_chat_message(session_id, "assistant", completion_message)
    
    return {
        "success": True,
        "completion_result": completion_result,
        "progress": get_implementation_progress(completed_tasks)
    }

@router.post("/sessions/{session_id}/implementation/tasks/{task_id}/upload-document")
async def upload_task_document(
    session_id: str,
    task_id: str,
    request: Request,
    file: UploadFile = File(...)
):
    """Upload document for task completion"""
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    task = await get_implementation_task(task_id, session)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Validate file type
    allowed_types = ["application/pdf", "application/msword", 
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "image/jpeg", "image/png"]
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload PDF, DOC, DOCX, JPEG, or PNG files.")
    
    # Create uploads directory if it doesn't exist
    import os
    upload_dir = f"uploads/implementation/{session_id}/{task_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    from datetime import datetime
    import uuid
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{file_extension}"
    
    # Save file
    file_path = os.path.join(upload_dir, unique_filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Save upload message to chat
    upload_message = f"📄 **Document Uploaded for {task['title']}**\n\n**File:** {file.filename}\n**Size:** {len(content)} bytes\n**Type:** {file.content_type}\n**Uploaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nDocument successfully uploaded for task completion verification."
    await save_chat_message(session_id, "assistant", upload_message)
    
    return {
        "success": True,
        "message": "Document uploaded successfully",
        "file_path": file_path,
        "file_info": {
            "filename": file.filename,
            "size": len(content),
            "type": file.content_type,
            "uploaded_at": datetime.now().isoformat()
        }
    }

@router.get("/sessions/{session_id}/implementation/progress")
async def get_implementation_progress_endpoint(session_id: str, request: Request):
    """Get implementation progress for a session"""
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    completed_tasks = session.get("completed_implementation_tasks", [])
    progress = get_implementation_progress(completed_tasks)
    
    return {
        "success": True,
        "progress": progress,
        "completed_tasks": completed_tasks
    }

@router.post("/sessions/{session_id}/implementation/help")
async def get_implementation_help(session_id: str, request: Request, help_request: Dict):
    """Get help for implementation tasks"""
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    task_id = help_request.get("task_id")
    help_type = help_request.get("help_type", "general")
    
    if task_id:
        task = await get_implementation_task(task_id, session)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Generate task-specific help
        help_prompt = f"""
        Provide comprehensive help for the implementation task: {task['title']}
        
        Task Details:
        - Description: {task['description']}
        - Purpose: {task['purpose']}
        - Options: {', '.join(task['options'])}
        
        Help Type: {help_type}
        
        Provide:
        1. Detailed explanation of the task
        2. Step-by-step guidance
        3. Common challenges and solutions
        4. Best practices
        5. Additional resources
        
        Make it actionable and supportive.
        """
        
        try:
            from services.angel_service import client
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are Angel, a helpful business implementation assistant."},
                    {"role": "user", "content": help_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            help_content = response.choices[0].message.content
            
            # Save help message to chat
            help_message = f"💡 **Help for {task['title']}**\n\n{help_content}"
            await save_chat_message(session_id, "assistant", help_message)
            
            return {
                "success": True,
                "help_content": help_content,
                "task": task
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating help: {str(e)}"
            }
    
    return {
        "success": True,
        "help_content": "General implementation help content",
        "message": "Please specify a task_id for specific help"
    }

@router.post("/sessions/{session_id}/implementation/contact")
async def get_implementation_contact(session_id: str, request: Request, contact_request: Dict):
    """Get contact information for service providers"""
    user_id = request.state.user["id"]
    session = await get_session(session_id, user_id)
    
    task_id = contact_request.get("task_id")
    
    if task_id:
        task = await get_implementation_task(task_id, session)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        service_providers = await generate_service_providers(task, session)
        
        # Save contact message to chat
        contact_message = f"📞 **Service Provider Contacts for {task['title']}**\n\n"
        for provider in service_providers:
            contact_message += f"**{provider['name']}** ({'Local' if provider['local'] else 'Online'})\n"
            contact_message += f"- Type: {provider['type']}\n"
            contact_message += f"- Description: {provider['description']}\n"
            contact_message += f"- Pricing: {provider['pricing']}\n"
            contact_message += f"- Website: {provider['website']}\n"
            contact_message += f"- Rating: {provider['rating']}/5\n\n"
        
        await save_chat_message(session_id, "assistant", contact_message)
        
        return {
            "success": True,
            "service_providers": service_providers,
            "task": task
        }
    
    return {
        "success": True,
        "message": "Please specify a task_id for specific service provider contacts"
    }
