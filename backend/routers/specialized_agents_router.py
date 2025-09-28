from fastapi import APIRouter, Request, Depends, HTTPException
from typing import Dict, List, Any, Optional
from services.specialized_agents_service import agents_manager, get_comprehensive_guidance
from services.rag_service import conduct_rag_research, validate_with_rag, generate_rag_insights, research_service_providers_rag
from services.service_provider_tables_service import generate_provider_table, get_task_providers
from middlewares.auth import verify_auth_token
from schemas.angel_schemas import ChatRequestSchema
import json

router = APIRouter(
    tags=["Specialized Agents & RAG"],
    dependencies=[Depends(verify_auth_token)]
)

@router.post("/sessions/{session_id}/agent-guidance")
async def get_agent_guidance(
    session_id: str,
    request: Request,
    payload: Dict[str, Any]
):
    """Get guidance from specialized agents"""
    
    user_id = request.state.user["id"]
    question = payload.get("question", "")
    agent_type = payload.get("agent_type", "comprehensive")  # or specific agent type
    business_context = payload.get("business_context", {})
    
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    try:
        if agent_type == "comprehensive":
            # Get guidance from all relevant agents
            guidance = await get_comprehensive_guidance(question, business_context, [])
        else:
            # Get guidance from specific agent
            guidance = await agents_manager.get_agent_guidance(agent_type, question, business_context, [])
        
        return {
            "success": True,
            "message": "Agent guidance generated successfully",
            "result": guidance
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent guidance: {str(e)}")

@router.get("/sessions/{session_id}/agents")
async def get_available_agents(session_id: str, request: Request):
    """Get information about available specialized agents"""
    
    try:
        agent_info = agents_manager.get_agent_info()
        
        return {
            "success": True,
            "message": "Available agents retrieved successfully",
            "result": {
                "agents": agent_info,
                "total_agents": len(agent_info)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent info: {str(e)}")

@router.post("/sessions/{session_id}/rag-research")
async def conduct_rag_research_endpoint(
    session_id: str,
    request: Request,
    payload: Dict[str, Any]
):
    """Conduct comprehensive RAG research"""
    
    user_id = request.state.user["id"]
    query = payload.get("query", "")
    business_context = payload.get("business_context", {})
    research_depth = payload.get("research_depth", "standard")  # basic, standard, comprehensive
    
    if not query:
        raise HTTPException(status_code=400, detail="Research query is required")
    
    try:
        research_results = await conduct_rag_research(query, business_context, research_depth)
        
        return {
            "success": True,
            "message": "RAG research completed successfully",
            "result": research_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to conduct RAG research: {str(e)}")

@router.post("/sessions/{session_id}/rag-validation")
async def validate_user_input_rag(
    session_id: str,
    request: Request,
    payload: Dict[str, Any]
):
    """Validate user input using RAG research"""
    
    user_id = request.state.user["id"]
    user_input = payload.get("user_input", "")
    question_type = payload.get("question_type", "general")
    business_context = payload.get("business_context", {})
    
    if not user_input:
        raise HTTPException(status_code=400, detail="User input is required")
    
    try:
        validation_results = await validate_with_rag(user_input, business_context, question_type)
        
        return {
            "success": True,
            "message": "Input validation completed successfully",
            "result": validation_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate input: {str(e)}")

@router.post("/sessions/{session_id}/rag-insights")
async def generate_educational_insights_rag(
    session_id: str,
    request: Request,
    payload: Dict[str, Any]
):
    """Generate educational insights using RAG"""
    
    user_id = request.state.user["id"]
    user_response = payload.get("user_response", "")
    question_context = payload.get("question_context", "")
    business_context = payload.get("business_context", {})
    
    if not user_response or not question_context:
        raise HTTPException(status_code=400, detail="User response and question context are required")
    
    try:
        insights = await generate_rag_insights(user_response, question_context, business_context)
        
        return {
            "success": True,
            "message": "Educational insights generated successfully",
            "result": {
                "insights": insights,
                "timestamp": request.state.timestamp if hasattr(request.state, 'timestamp') else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

@router.post("/sessions/{session_id}/service-providers")
async def get_service_providers(
    session_id: str,
    request: Request,
    payload: Dict[str, Any]
):
    """Get service providers using RAG research"""
    
    user_id = request.state.user["id"]
    service_type = payload.get("service_type", "")
    business_context = payload.get("business_context", {})
    location = payload.get("location", None)
    
    if not service_type:
        raise HTTPException(status_code=400, detail="Service type is required")
    
    try:
        providers = await research_service_providers_rag(service_type, business_context, location)
        
        return {
            "success": True,
            "message": "Service providers retrieved successfully",
            "result": providers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service providers: {str(e)}")

@router.post("/sessions/{session_id}/provider-table")
async def generate_service_provider_table_endpoint(
    session_id: str,
    request: Request,
    payload: Dict[str, Any]
):
    """Generate comprehensive service provider table"""
    
    user_id = request.state.user["id"]
    task_context = payload.get("task_context", "")
    business_context = payload.get("business_context", {})
    location = payload.get("location", None)
    
    if not task_context:
        raise HTTPException(status_code=400, detail="Task context is required")
    
    try:
        provider_table = await generate_provider_table(task_context, business_context, location)
        
        return {
            "success": True,
            "message": "Service provider table generated successfully",
            "result": provider_table
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate provider table: {str(e)}")

@router.post("/sessions/{session_id}/task-providers")
async def get_task_specific_providers(
    session_id: str,
    request: Request,
    payload: Dict[str, Any]
):
    """Get providers for a specific implementation task"""
    
    user_id = request.state.user["id"]
    task_id = payload.get("task_id", "")
    task_description = payload.get("task_description", "")
    business_context = payload.get("business_context", {})
    location = payload.get("location", None)
    
    if not task_id or not task_description:
        raise HTTPException(status_code=400, detail="Task ID and description are required")
    
    try:
        task_providers = await get_task_providers(task_id, task_description, business_context, location)
        
        return {
            "success": True,
            "message": "Task-specific providers retrieved successfully",
            "result": task_providers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task providers: {str(e)}")

@router.post("/sessions/{session_id}/comprehensive-support")
async def get_comprehensive_support(
    session_id: str,
    request: Request,
    payload: Dict[str, Any]
):
    """Get comprehensive support combining agents, RAG, and service providers"""
    
    user_id = request.state.user["id"]
    question = payload.get("question", "")
    task_context = payload.get("task_context", "")
    business_context = payload.get("business_context", {})
    location = payload.get("location", None)
    
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    try:
        # Get agent guidance
        agent_guidance = await get_comprehensive_guidance(question, business_context, [])
        
        # Conduct RAG research
        rag_research = await conduct_rag_research(question, business_context, "standard")
        
        # Generate service provider table if task context provided
        provider_table = None
        if task_context:
            provider_table = await generate_provider_table(task_context, business_context, location)
        
        # Combine all results
        comprehensive_support = {
            "question": question,
            "task_context": task_context,
            "business_context": business_context,
            "agent_guidance": agent_guidance,
            "rag_research": rag_research,
            "provider_table": provider_table,
            "timestamp": request.state.timestamp if hasattr(request.state, 'timestamp') else None
        }
        
        return {
            "success": True,
            "message": "Comprehensive support generated successfully",
            "result": comprehensive_support
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate comprehensive support: {str(e)}")

@router.get("/sessions/{session_id}/research-sources")
async def get_research_sources(session_id: str, request: Request):
    """Get information about research sources used by RAG"""
    
    try:
        from services.rag_service import rag_engine
        
        research_sources = {
            "authoritative_sources": rag_engine.authoritative_sources,
            "total_categories": len(rag_engine.authoritative_sources),
            "total_sources": sum(len(sources) for sources in rag_engine.authoritative_sources.values())
        }
        
        return {
            "success": True,
            "message": "Research sources retrieved successfully",
            "result": research_sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get research sources: {str(e)}")

@router.post("/sessions/{session_id}/interactive-command")
async def handle_interactive_command(
    session_id: str,
    request: Request,
    payload: Dict[str, Any]
):
    """Handle interactive commands with specialized support"""
    
    user_id = request.state.user["id"]
    command = payload.get("command", "").lower()
    context = payload.get("context", "")
    business_context = payload.get("business_context", {})
    
    if not command:
        raise HTTPException(status_code=400, detail="Command is required")
    
    try:
        response = {}
        
        if command == "help":
            # Get comprehensive help using agents
            help_guidance = await get_comprehensive_guidance(
                f"Provide detailed help for: {context}",
                business_context,
                []
            )
            response = {
                "command": "help",
                "guidance": help_guidance,
                "type": "comprehensive_guidance"
            }
        
        elif command == "who do i contact?":
            # Get service provider recommendations
            if context:
                providers = await research_service_providers_rag(context, business_context)
                response = {
                    "command": "contact",
                    "providers": providers,
                    "type": "service_providers"
                }
            else:
                response = {
                    "command": "contact",
                    "message": "Please specify what type of service you need help with",
                    "type": "clarification_needed"
                }
        
        elif command == "scrapping":
            # Get refined guidance using RAG
            if context:
                insights = await generate_rag_insights(context, "idea refinement", business_context)
                response = {
                    "command": "scrapping",
                    "refined_insights": insights,
                    "type": "refined_guidance"
                }
            else:
                response = {
                    "command": "scrapping",
                    "message": "Please provide the ideas you'd like me to help refine",
                    "type": "clarification_needed"
                }
        
        elif command == "draft":
            # Generate draft using agents and RAG
            if context:
                draft_guidance = await get_comprehensive_guidance(
                    f"Create a comprehensive draft for: {context}",
                    business_context,
                    []
                )
                response = {
                    "command": "draft",
                    "draft_content": draft_guidance,
                    "type": "draft_content"
                }
            else:
                response = {
                    "command": "draft",
                    "message": "Please specify what you'd like me to draft",
                    "type": "clarification_needed"
                }
        
        elif command == "kickstart":
            # Generate kickstart plan with providers
            if context:
                kickstart_guidance = await get_comprehensive_guidance(
                    f"Create a kickstart plan for: {context}",
                    business_context,
                    []
                )
                provider_table = await generate_provider_table(context, business_context)
                response = {
                    "command": "kickstart",
                    "kickstart_plan": kickstart_guidance,
                    "provider_table": provider_table,
                    "type": "kickstart_plan"
                }
            else:
                response = {
                    "command": "kickstart",
                    "message": "Please specify what you'd like me to help kickstart",
                    "type": "clarification_needed"
                }
        
        else:
            response = {
                "command": command,
                "message": f"Unknown command: {command}. Available commands: help, who do i contact?, scrapping, draft, kickstart",
                "type": "unknown_command"
            }
        
        return {
            "success": True,
            "message": f"Command '{command}' processed successfully",
            "result": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process command: {str(e)}")
