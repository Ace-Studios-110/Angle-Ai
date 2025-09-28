from fastapi import APIRouter, Request, Depends, HTTPException
from typing import Dict, List, Any, Optional
from services.appendices_integration_service import (
    appendices_integration_service,
    get_comprehensive_ux_data,
    process_completion_declaration,
    generate_dynamic_prompts,
    ProgressIndicator,
    DynamicPrompt,
    InteractiveCommand,
    NavigationItem,
    CompletionDeclaration
)
from services.credible_resources_service import credible_resources_manager, get_credible_resources_for_query
from services.deep_research_training_service import deep_research_training_manager, conduct_agent_deep_research, AgentType
from middlewares.auth import verify_auth_token
from datetime import datetime
import json

router = APIRouter(
    tags=["Appendices Integration"],
    dependencies=[Depends(verify_auth_token)]
)

@router.get("/sessions/{session_id}/ux-data")
async def get_comprehensive_ux_data_endpoint(session_id: str, request: Request):
    """Get comprehensive UX data integrating all appendices"""
    
    user_id = request.state.user["id"]
    
    try:
        # Get business context (you'll need to implement this based on your session service)
        business_context = {
            "business_name": "Your Business",
            "industry": "Technology",
            "location": "San Francisco, CA",
            "business_type": "Startup"
        }
        
        # Get current task (you'll need to implement this based on your session service)
        current_task = "business_structure_selection"
        
        # Get comprehensive UX data
        ux_data = await get_comprehensive_ux_data(session_id, business_context, current_task)
        
        return {
            "success": True,
            "message": "Comprehensive UX data retrieved successfully",
            "data": ux_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get UX data: {str(e)}")

@router.get("/sessions/{session_id}/progress-indicators")
async def get_progress_indicators(session_id: str, request: Request):
    """Get progress indicators for a session"""
    
    user_id = request.state.user["id"]
    
    try:
        business_context = {
            "business_name": "Your Business",
            "industry": "Technology",
            "location": "San Francisco, CA",
            "business_type": "Startup"
        }
        
        progress_indicators = await appendices_integration_service.get_comprehensive_progress_indicators(session_id, business_context)
        
        return {
            "success": True,
            "message": "Progress indicators retrieved successfully",
            "indicators": [
                {
                    "id": p.id,
                    "label": p.label,
                    "progress": p.progress,
                    "type": p.type.value,
                    "status": p.status,
                    "phase": p.phase,
                    "section": p.section,
                    "last_updated": p.last_updated.isoformat() if p.last_updated else None
                }
                for p in progress_indicators
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress indicators: {str(e)}")

@router.get("/sessions/{session_id}/dynamic-prompts")
async def get_dynamic_prompts(session_id: str, request: Request, current_task: Optional[str] = None):
    """Get dynamic prompts for a session"""
    
    user_id = request.state.user["id"]
    
    try:
        business_context = {
            "business_name": "Your Business",
            "industry": "Technology",
            "location": "San Francisco, CA",
            "business_type": "Startup"
        }
        
        prompts = await generate_dynamic_prompts(session_id, business_context, current_task)
        
        return {
            "success": True,
            "message": "Dynamic prompts retrieved successfully",
            "prompts": [
                {
                    "id": p.id,
                    "type": p.type.value,
                    "title": p.title,
                    "message": p.message,
                    "action_label": p.action_label,
                    "action_command": p.action_command,
                    "dismissible": p.dismissible,
                    "priority": p.priority,
                    "expires_at": p.expires_at.isoformat() if p.expires_at else None
                }
                for p in prompts
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dynamic prompts: {str(e)}")

@router.get("/sessions/{session_id}/interactive-commands")
async def get_interactive_commands(session_id: str, request: Request, current_task: Optional[str] = None):
    """Get interactive commands for a session"""
    
    user_id = request.state.user["id"]
    
    try:
        business_context = {
            "business_name": "Your Business",
            "industry": "Technology",
            "location": "San Francisco, CA",
            "business_type": "Startup"
        }
        
        commands = await appendices_integration_service.get_interactive_commands(session_id, business_context, current_task)
        
        return {
            "success": True,
            "message": "Interactive commands retrieved successfully",
            "commands": [
                {
                    "command": c.command.value,
                    "description": c.description,
                    "available": c.available,
                    "requires_context": c.requires_context,
                    "agent_support": c.agent_support.value if c.agent_support else None
                }
                for c in commands
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get interactive commands: {str(e)}")

@router.get("/sessions/{session_id}/navigation")
async def get_flexible_navigation(session_id: str, request: Request):
    """Get flexible navigation structure for a session"""
    
    user_id = request.state.user["id"]
    
    try:
        business_context = {
            "business_name": "Your Business",
            "industry": "Technology",
            "location": "San Francisco, CA",
            "business_type": "Startup"
        }
        
        navigation_items = await appendices_integration_service.get_flexible_navigation(session_id, business_context)
        
        return {
            "success": True,
            "message": "Navigation structure retrieved successfully",
            "navigation": [
                {
                    "id": n.id,
                    "label": n.label,
                    "phase": n.phase,
                    "status": n.status,
                    "description": n.description,
                    "tasks": n.tasks,
                    "prerequisites": n.prerequisites
                }
                for n in navigation_items
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get navigation: {str(e)}")

@router.post("/sessions/{session_id}/completion-declaration")
async def process_completion_declaration_endpoint(session_id: str, request: Request, declaration_data: Dict[str, Any]):
    """Process a completion declaration"""
    
    user_id = request.state.user["id"]
    
    try:
        business_context = {
            "business_name": "Your Business",
            "industry": "Technology",
            "location": "San Francisco, CA",
            "business_type": "Startup"
        }
        
        # Create completion declaration object
        declaration = CompletionDeclaration(
            task_id=declaration_data.get("task_id"),
            summary=declaration_data.get("summary"),
            decisions=declaration_data.get("decisions", []),
            actions_taken=declaration_data.get("actions_taken", []),
            documents_uploaded=declaration_data.get("documents_uploaded", []),
            completion_date=datetime.now(),
            next_steps=declaration_data.get("next_steps", [])
        )
        
        # Process the declaration
        result = await process_completion_declaration(session_id, declaration, business_context)
        
        return {
            "success": True,
            "message": "Completion declaration processed successfully",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process completion declaration: {str(e)}")

@router.get("/credible-resources")
async def get_credible_resources(request: Request, category: Optional[str] = None, jurisdiction: Optional[str] = None):
    """Get credible resources and data sources"""
    
    user_id = request.state.user["id"]
    
    try:
        if category:
            resources = await credible_resources_manager.get_resources_by_category(category)
        elif jurisdiction:
            resources = await credible_resources_manager.get_resources_by_jurisdiction(jurisdiction)
        else:
            resources = list(credible_resources_manager.resources.values())
        
        return {
            "success": True,
            "message": "Credible resources retrieved successfully",
            "resources": [
                {
                    "name": r.name,
                    "url": r.url,
                    "resource_type": r.resource_type.value,
                    "credibility_level": r.credibility_level.value,
                    "description": r.description,
                    "jurisdiction": r.jurisdiction,
                    "categories": r.categories,
                    "last_verified": r.last_verified.isoformat() if r.last_verified else None
                }
                for r in resources
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get credible resources: {str(e)}")

@router.post("/credible-resources/research")
async def conduct_credible_research(request: Request, research_request: Dict[str, Any]):
    """Conduct research using credible resources"""
    
    user_id = request.state.user["id"]
    
    try:
        query = research_request.get("query")
        business_context = research_request.get("business_context", {})
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Get credible resources for the query
        resources_data = await get_credible_resources_for_query(query, business_context)
        
        return {
            "success": True,
            "message": "Credible research conducted successfully",
            "research_data": resources_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to conduct credible research: {str(e)}")

@router.get("/agent-training-data/{agent_type}")
async def get_agent_training_data(agent_type: str, request: Request):
    """Get training data for a specific agent"""
    
    user_id = request.state.user["id"]
    
    try:
        # Convert string to AgentType enum
        try:
            agent_enum = AgentType(agent_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid agent type: {agent_type}")
        
        training_data = await deep_research_training_manager.get_agent_training_data(agent_enum)
        
        return {
            "success": True,
            "message": "Agent training data retrieved successfully",
            "training_data": {
                "agent_type": training_data.agent_type.value,
                "knowledge_domains": training_data.knowledge_domains,
                "credible_sources": training_data.credible_sources,
                "expertise_areas": training_data.expertise_areas,
                "training_queries": training_data.training_queries,
                "validation_criteria": training_data.validation_criteria
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent training data: {str(e)}")

@router.post("/agent-deep-research")
async def conduct_agent_deep_research_endpoint(request: Request, research_request: Dict[str, Any]):
    """Conduct deep research using agent training data"""
    
    user_id = request.state.user["id"]
    
    try:
        agent_type_str = research_request.get("agent_type")
        query = research_request.get("query")
        business_context = research_request.get("business_context", {})
        
        if not agent_type_str or not query:
            raise HTTPException(status_code=400, detail="Agent type and query are required")
        
        # Convert string to AgentType enum
        try:
            agent_type = AgentType(agent_type_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid agent type: {agent_type_str}")
        
        # Conduct deep research
        research_results = await conduct_agent_deep_research(agent_type, query, business_context)
        
        return {
            "success": True,
            "message": "Agent deep research conducted successfully",
            "research_results": research_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to conduct agent deep research: {str(e)}")

@router.post("/sessions/{session_id}/execute-command")
async def execute_interactive_command(session_id: str, request: Request, command_data: Dict[str, Any]):
    """Execute an interactive command"""
    
    user_id = request.state.user["id"]
    
    try:
        command = command_data.get("command")
        context = command_data.get("context", {})
        
        if not command:
            raise HTTPException(status_code=400, detail="Command is required")
        
        business_context = {
            "business_name": "Your Business",
            "industry": "Technology",
            "location": "San Francisco, CA",
            "business_type": "Startup"
        }
        
        # Execute command based on type
        if command == "help":
            # Get help from relevant agent
            agent_guidance = await agents_manager.get_multi_agent_guidance(
                context.get("question", "General help request"),
                business_context,
                []
            )
            result = {"type": "help", "guidance": agent_guidance}
            
        elif command == "contact":
            # Get service providers
            from services.service_provider_tables_service import generate_provider_table
            provider_table = await generate_provider_table(
                context.get("query", "service providers"),
                business_context,
                business_context.get("location")
            )
            result = {"type": "contact", "providers": provider_table}
            
        elif command == "scrapping":
            # Conduct research
            from services.rag_service import conduct_rag_research
            rag_research = await conduct_rag_research(
                context.get("query", "business research"),
                business_context,
                "standard"
            )
            result = {"type": "scrapping", "research": rag_research}
            
        elif command == "draft":
            # Generate documents
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Draft: {context.get('document_type', 'business document')}"}],
                temperature=0.3,
                max_tokens=1500
            )
            
            result = {"type": "draft", "document": response.choices[0].message.content}
            
        elif command == "kickstart":
            # Generate action plan
            kickstart_guidance = await agents_manager.get_multi_agent_guidance(
                f"Create kickstart plan for: {context.get('task', 'current task')}",
                business_context,
                []
            )
            result = {"type": "kickstart", "plan": kickstart_guidance}
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown command: {command}")
        
        return {
            "success": True,
            "message": f"Command '{command}' executed successfully",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute command: {str(e)}")

@router.get("/sessions/{session_id}/dismiss-prompt/{prompt_id}")
async def dismiss_dynamic_prompt(session_id: str, prompt_id: str, request: Request):
    """Dismiss a dynamic prompt"""
    
    user_id = request.state.user["id"]
    
    try:
        # In a real implementation, you would store dismissed prompts in your database
        # For now, we'll just return success
        
        return {
            "success": True,
            "message": f"Prompt '{prompt_id}' dismissed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to dismiss prompt: {str(e)}")

@router.get("/sessions/{session_id}/navigate/{phase}")
async def navigate_to_phase(session_id: str, phase: str, request: Request):
    """Navigate to a specific phase"""
    
    user_id = request.state.user["id"]
    
    try:
        # In a real implementation, you would update the session's current phase
        # For now, we'll just return success
        
        return {
            "success": True,
            "message": f"Navigated to phase '{phase}' successfully",
            "current_phase": phase
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to navigate to phase: {str(e)}")
