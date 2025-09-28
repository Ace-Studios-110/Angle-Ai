import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
from services.credible_resources_service import credible_resources_manager, CredibleResource, ResourceType, CredibilityLevel
from services.deep_research_training_service import deep_research_training_manager, AgentType, AgentTrainingData
from services.specialized_agents_service import agents_manager
from services.rag_service import conduct_rag_research, validate_with_rag, generate_rag_insights

logger = logging.getLogger(__name__)

class ProgressType(Enum):
    OVERALL = "overall"
    SECTION = "section"
    TASK = "task"

class PromptType(Enum):
    NOTIFICATION = "notification"
    REMINDER = "reminder"
    SUGGESTION = "suggestion"
    WARNING = "warning"
    SUCCESS = "success"

class CommandType(Enum):
    HELP = "help"
    CONTACT = "contact"
    SCRAPPING = "scrapping"
    DRAFT = "draft"
    KICKSTART = "kickstart"

@dataclass
class ProgressIndicator:
    id: str
    label: str
    progress: float
    type: ProgressType
    status: str
    phase: Optional[str] = None
    section: Optional[str] = None
    last_updated: Optional[datetime] = None

@dataclass
class DynamicPrompt:
    id: str
    type: PromptType
    title: str
    message: str
    action_label: Optional[str] = None
    action_command: Optional[str] = None
    dismissible: bool = True
    priority: str = "medium"
    expires_at: Optional[datetime] = None
    business_context: Optional[Dict[str, Any]] = None

@dataclass
class InteractiveCommand:
    command: CommandType
    description: str
    available: bool
    requires_context: bool = False
    agent_support: Optional[AgentType] = None

@dataclass
class NavigationItem:
    id: str
    label: str
    phase: str
    status: str
    description: Optional[str] = None
    tasks: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None

@dataclass
class CompletionDeclaration:
    task_id: str
    summary: str
    decisions: List[str]
    actions_taken: List[str]
    documents_uploaded: List[str]
    completion_date: datetime
    next_steps: List[str]
    validation_results: Optional[Dict[str, Any]] = None

class AppendicesIntegrationService:
    """Integrates all three appendices: Credible Resources, Agentic Architecture, and UX Guidelines"""
    
    def __init__(self):
        self.session_progress = {}
        self.session_prompts = {}
        self.session_navigation = {}
        self.completion_declarations = {}
    
    async def get_comprehensive_progress_indicators(self, session_id: str, business_context: Dict[str, Any]) -> List[ProgressIndicator]:
        """Get comprehensive progress indicators for a session"""
        
        # Get overall progress
        overall_progress = await self._calculate_overall_progress(session_id)
        
        # Get section-specific progress
        section_progress = await self._calculate_section_progress(session_id, business_context)
        
        # Get task-specific progress
        task_progress = await self._calculate_task_progress(session_id, business_context)
        
        return [overall_progress] + section_progress + task_progress
    
    async def _calculate_overall_progress(self, session_id: str) -> ProgressIndicator:
        """Calculate overall workflow progress"""
        
        # This would typically query your database for actual progress
        # For now, we'll simulate progress calculation
        phases_completed = 2  # KYC, Business Plan
        total_phases = 4  # KYC, Business Plan, Roadmap, Implementation
        
        progress_percent = int((phases_completed / total_phases) * 100)
        
        return ProgressIndicator(
            id="overall_progress",
            label="Overall Workflow Progress",
            progress=progress_percent,
            type=ProgressType.OVERALL,
            status="in_progress",
            last_updated=datetime.now()
        )
    
    async def _calculate_section_progress(self, session_id: str, business_context: Dict[str, Any]) -> List[ProgressIndicator]:
        """Calculate section-specific progress"""
        
        sections = [
            ("kyc_section", "KYC Intake Questionnaire", 100, "completed"),
            ("planning_section", "Business Plan Development", 100, "completed"),
            ("roadmap_section", "Launch Roadmap Creation", 75, "in_progress"),
            ("implementation_section", "Implementation Execution", 0, "pending")
        ]
        
        indicators = []
        for section_id, label, progress, status in sections:
            indicators.append(ProgressIndicator(
                id=section_id,
                label=label,
                progress=progress,
                type=ProgressType.SECTION,
                status=status,
                section=section_id,
                last_updated=datetime.now()
            ))
        
        return indicators
    
    async def _calculate_task_progress(self, session_id: str, business_context: Dict[str, Any]) -> List[ProgressIndicator]:
        """Calculate task-specific progress"""
        
        # Get current phase tasks
        current_phase = await self._get_current_phase(session_id)
        
        if current_phase == "ROADMAP":
            tasks = [
                ("market_research", "Market Research & Analysis", 100, "completed"),
                ("competitive_analysis", "Competitive Analysis", 100, "completed"),
                ("timeline_creation", "Timeline Creation", 50, "in_progress"),
                ("resource_planning", "Resource Planning", 0, "pending")
            ]
        elif current_phase == "IMPLEMENTATION":
            tasks = [
                ("legal_formation", "Legal Formation", 0, "pending"),
                ("financial_setup", "Financial Setup", 0, "pending"),
                ("operations_setup", "Operations Setup", 0, "pending"),
                ("marketing_setup", "Marketing Setup", 0, "pending")
            ]
        else:
            tasks = []
        
        indicators = []
        for task_id, label, progress, status in tasks:
            indicators.append(ProgressIndicator(
                id=task_id,
                label=label,
                progress=progress,
                type=ProgressType.TASK,
                status=status,
                phase=current_phase,
                last_updated=datetime.now()
            ))
        
        return indicators
    
    async def generate_dynamic_prompts(self, session_id: str, business_context: Dict[str, Any], current_task: Optional[str] = None) -> List[DynamicPrompt]:
        """Generate dynamic prompts based on current state and progress"""
        
        prompts = []
        
        # Progress-based prompts
        progress_indicators = await self.get_comprehensive_progress_indicators(session_id, business_context)
        overall_progress = next((p for p in progress_indicators if p.type == ProgressType.OVERALL), None)
        
        if overall_progress:
            if overall_progress.progress >= 50:
                prompts.append(DynamicPrompt(
                    id="progress_milestone",
                    type=PromptType.SUCCESS,
                    title="Excellent Progress!",
                    message=f"You've completed {overall_progress.progress}% of your entrepreneurial journey. You're making great strides toward building your dream business!",
                    dismissible=True,
                    priority="medium",
                    business_context=business_context
                ))
            
            if overall_progress.progress >= 75:
                prompts.append(DynamicPrompt(
                    id="near_completion",
                    type=PromptType.NOTIFICATION,
                    title="Almost There!",
                    message="You're in the final stretch! Consider using the 'Kickstart' command to accelerate your remaining tasks.",
                    action_label="Get Kickstart Plan",
                    action_command="kickstart",
                    dismissible=True,
                    priority="high",
                    business_context=business_context
                ))
        
        # Task-specific prompts
        if current_task:
            task_prompts = await self._generate_task_specific_prompts(current_task, business_context)
            prompts.extend(task_prompts)
        
        # Phase-specific prompts
        current_phase = await self._get_current_phase(session_id)
        phase_prompts = await self._generate_phase_specific_prompts(current_phase, business_context)
        prompts.extend(phase_prompts)
        
        # Business context prompts
        context_prompts = await self._generate_context_specific_prompts(business_context)
        prompts.extend(context_prompts)
        
        return prompts
    
    async def _generate_task_specific_prompts(self, task: str, business_context: Dict[str, Any]) -> List[DynamicPrompt]:
        """Generate prompts specific to current task"""
        
        prompts = []
        
        if "legal" in task.lower():
            prompts.append(DynamicPrompt(
                id="legal_reminder",
                type=PromptType.REMINDER,
                title="Legal Compliance Reminder",
                message="Remember to research jurisdiction-specific requirements for your business location. Use 'Who do I contact?' to find local legal professionals.",
                action_label="Find Legal Help",
                action_command="contact",
                dismissible=True,
                priority="high",
                business_context=business_context
            ))
        
        if "financial" in task.lower():
            prompts.append(DynamicPrompt(
                id="financial_tip",
                type=PromptType.SUGGESTION,
                title="Financial Planning Tip",
                message="Consider using 'Draft' to create financial templates and 'Scrapping' to research funding options specific to your industry.",
                dismissible=True,
                priority="medium",
                business_context=business_context
            ))
        
        return prompts
    
    async def _generate_phase_specific_prompts(self, phase: str, business_context: Dict[str, Any]) -> List[DynamicPrompt]:
        """Generate prompts specific to current phase"""
        
        prompts = []
        
        if phase == "IMPLEMENTATION":
            prompts.append(DynamicPrompt(
                id="implementation_guidance",
                type=PromptType.NOTIFICATION,
                title="Implementation Phase Started",
                message="You're now in the implementation phase! Remember to declare task completions and upload documentation to keep your progress updated.",
                dismissible=True,
                priority="high",
                business_context=business_context
            ))
        
        return prompts
    
    async def _generate_context_specific_prompts(self, business_context: Dict[str, Any]) -> List[DynamicPrompt]:
        """Generate prompts based on business context"""
        
        prompts = []
        
        industry = business_context.get('industry', '').lower()
        location = business_context.get('location', '').lower()
        
        if 'tech' in industry or 'software' in industry:
            prompts.append(DynamicPrompt(
                id="tech_industry_tip",
                type=PromptType.SUGGESTION,
                title="Tech Industry Insight",
                message="For technology businesses, consider using 'Scrapping' to research latest industry trends and 'Draft' to create technical documentation.",
                dismissible=True,
                priority="medium",
                business_context=business_context
            ))
        
        if 'california' in location.lower():
            prompts.append(DynamicPrompt(
                id="california_compliance",
                type=PromptType.WARNING,
                title="California Compliance",
                message="California has specific business requirements. Use 'Who do I contact?' to find California-specific service providers.",
                dismissible=True,
                priority="high",
                business_context=business_context
            ))
        
        return prompts
    
    async def get_interactive_commands(self, session_id: str, business_context: Dict[str, Any], current_task: Optional[str] = None) -> List[InteractiveCommand]:
        """Get available interactive commands for current context"""
        
        commands = [
            InteractiveCommand(
                command=CommandType.HELP,
                description="Get detailed assistance and guidance",
                available=True,
                requires_context=True,
                agent_support=AgentType.BUSINESS_STRATEGY
            ),
            InteractiveCommand(
                command=CommandType.CONTACT,
                description="Find service providers and contacts",
                available=True,
                requires_context=True,
                agent_support=AgentType.LEGAL_COMPLIANCE
            ),
            InteractiveCommand(
                command=CommandType.SCRAPPING,
                description="Research and analyze information",
                available=True,
                requires_context=True,
                agent_support=AgentType.BUSINESS_STRATEGY
            ),
            InteractiveCommand(
                command=CommandType.DRAFT,
                description="Create documents and templates",
                available=True,
                requires_context=True,
                agent_support=AgentType.LEGAL_COMPLIANCE
            ),
            InteractiveCommand(
                command=CommandType.KICKSTART,
                description="Get detailed action plan",
                available=True,
                requires_context=True,
                agent_support=AgentType.ROADMAP_EXECUTION
            )
        ]
        
        # Filter commands based on current context
        if current_task:
            # Some commands might be more relevant for specific tasks
            pass
        
        return commands
    
    async def get_flexible_navigation(self, session_id: str, business_context: Dict[str, Any]) -> List[NavigationItem]:
        """Get flexible navigation structure"""
        
        navigation_items = [
            NavigationItem(
                id="kyc",
                label="KYC Intake Questionnaire",
                phase="KYC",
                status="completed",
                description="Initial business information gathering",
                tasks=["business_info", "industry_analysis", "market_research"]
            ),
            NavigationItem(
                id="business_plan",
                label="Business Plan Development",
                phase="PLANNING",
                status="completed",
                description="Comprehensive business planning",
                tasks=["executive_summary", "market_analysis", "financial_projections", "operations_plan"]
            ),
            NavigationItem(
                id="roadmap",
                label="Launch Roadmap",
                phase="ROADMAPPING",
                status="current",
                description="Step-by-step implementation plan",
                tasks=["timeline_creation", "resource_planning", "milestone_definition", "risk_assessment"]
            ),
            NavigationItem(
                id="implementation",
                label="Implementation Phase",
                phase="IMPLEMENTATION",
                status="upcoming",
                description="Execute your business plan",
                tasks=["legal_formation", "financial_setup", "operations_setup", "marketing_setup"],
                prerequisites=["roadmap"]
            )
        ]
        
        return navigation_items
    
    async def process_completion_declaration(self, session_id: str, declaration: CompletionDeclaration, business_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a completion declaration with validation"""
        
        # Validate completion using RAG research
        validation_query = f"Validate completion of {declaration.task_id}: {declaration.summary}"
        validation_results = await validate_with_rag(
            json.dumps({
                "task_id": declaration.task_id,
                "summary": declaration.summary,
                "decisions": declaration.decisions,
                "actions_taken": declaration.actions_taken
            }),
            business_context,
            f"completion_validation_{declaration.task_id}"
        )
        
        # Get agent feedback
        relevant_agent = await self._determine_relevant_agent(declaration.task_id)
        agent_feedback = None
        
        if relevant_agent:
            agent_guidance = await agents_manager.get_agent_guidance(
                f"Review completion of {declaration.task_id}",
                business_context,
                relevant_agent.value
            )
            agent_feedback = agent_guidance.get('guidance', '')
        
        # Store completion declaration
        self.completion_declarations[session_id] = self.completion_declarations.get(session_id, [])
        self.completion_declarations[session_id].append(declaration)
        
        # Generate next steps recommendations
        next_steps = await self._generate_next_steps_recommendations(declaration, business_context)
        
        return {
            "success": True,
            "declaration": declaration,
            "validation_results": validation_results,
            "agent_feedback": agent_feedback,
            "next_steps": next_steps,
            "completion_score": self._calculate_completion_score(declaration),
            "processed_at": datetime.now().isoformat()
        }
    
    async def _determine_relevant_agent(self, task_id: str) -> Optional[AgentType]:
        """Determine which agent is most relevant for a task"""
        
        task_lower = task_id.lower()
        
        if any(term in task_lower for term in ['legal', 'compliance', 'permit', 'license']):
            return AgentType.LEGAL_COMPLIANCE
        elif any(term in task_lower for term in ['financial', 'funding', 'budget', 'accounting']):
            return AgentType.FINANCIAL_PLANNING
        elif any(term in task_lower for term in ['operations', 'supply', 'equipment', 'process']):
            return AgentType.PRODUCT_OPERATIONS
        elif any(term in task_lower for term in ['marketing', 'branding', 'customer', 'advertising']):
            return AgentType.MARKETING_CUSTOMER
        elif any(term in task_lower for term in ['strategy', 'market', 'competitive', 'business_model']):
            return AgentType.BUSINESS_STRATEGY
        elif any(term in task_lower for term in ['roadmap', 'milestone', 'execution', 'scaling']):
            return AgentType.ROADMAP_EXECUTION
        
        return None
    
    async def _generate_next_steps_recommendations(self, declaration: CompletionDeclaration, business_context: Dict[str, Any]) -> List[str]:
        """Generate next steps recommendations based on completion"""
        
        # Use RAG research to generate contextual next steps
        research_query = f"Next steps after completing {declaration.task_id} for {business_context.get('industry', 'business')}"
        rag_research = await conduct_rag_research(research_query, business_context, "standard")
        
        # Generate recommendations using AI
        recommendations = [
            "Review and validate your completed work",
            "Update your progress tracking system",
            "Plan your next implementation task",
            "Consider any dependencies or prerequisites"
        ]
        
        # Add context-specific recommendations
        if declaration.task_id == "legal_formation":
            recommendations.extend([
                "Set up your business bank account",
                "Apply for necessary permits and licenses",
                "Consider business insurance options"
            ])
        elif declaration.task_id == "financial_setup":
            recommendations.extend([
                "Begin operational planning",
                "Start building your team",
                "Develop your marketing strategy"
            ])
        
        return recommendations
    
    def _calculate_completion_score(self, declaration: CompletionDeclaration) -> float:
        """Calculate a completion score based on declaration quality"""
        
        score = 0.0
        
        # Summary quality
        if declaration.summary and len(declaration.summary) > 50:
            score += 0.3
        
        # Decisions made
        if declaration.decisions and len(declaration.decisions) > 0:
            score += 0.2
        
        # Actions taken
        if declaration.actions_taken and len(declaration.actions_taken) > 0:
            score += 0.2
        
        # Documentation uploaded
        if declaration.documents_uploaded and len(declaration.documents_uploaded) > 0:
            score += 0.2
        
        # Next steps planned
        if declaration.next_steps and len(declaration.next_steps) > 0:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _get_current_phase(self, session_id: str) -> str:
        """Get current phase for a session"""
        
        # This would typically query your database
        # For now, we'll simulate based on session data
        return "ROADMAP"  # or "IMPLEMENTATION", "PLANNING", etc.
    
    async def get_comprehensive_ux_data(self, session_id: str, business_context: Dict[str, Any], current_task: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive UX data integrating all appendices"""
        
        # Get all UX components
        progress_indicators = await self.get_comprehensive_progress_indicators(session_id, business_context)
        dynamic_prompts = await self.generate_dynamic_prompts(session_id, business_context, current_task)
        interactive_commands = await self.get_interactive_commands(session_id, business_context, current_task)
        navigation_items = await self.get_flexible_navigation(session_id, business_context)
        
        # Get credible resources for current context
        credible_resources = await credible_resources_manager.get_comprehensive_research_sources(
            current_task or "business development",
            business_context
        )
        
        # Get agent training data
        agent_training_data = {}
        for agent_type in AgentType:
            training_data = await deep_research_training_manager.get_agent_training_data(agent_type)
            agent_training_data[agent_type.value] = {
                "expertise_areas": training_data.expertise_areas,
                "knowledge_domains": training_data.knowledge_domains,
                "credible_sources": training_data.credible_sources
            }
        
        return {
            "session_id": session_id,
            "business_context": business_context,
            "progress_indicators": [
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
            ],
            "dynamic_prompts": [
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
                for p in dynamic_prompts
            ],
            "interactive_commands": [
                {
                    "command": c.command.value,
                    "description": c.description,
                    "available": c.available,
                    "requires_context": c.requires_context,
                    "agent_support": c.agent_support.value if c.agent_support else None
                }
                for c in interactive_commands
            ],
            "navigation_items": [
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
            ],
            "credible_resources": credible_resources,
            "agent_training_data": agent_training_data,
            "generated_at": datetime.now().isoformat()
        }

# Global instance
appendices_integration_service = AppendicesIntegrationService()

# Convenience functions
async def get_comprehensive_ux_data(session_id: str, business_context: Dict[str, Any], current_task: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive UX data"""
    return await appendices_integration_service.get_comprehensive_ux_data(session_id, business_context, current_task)

async def process_completion_declaration(session_id: str, declaration: CompletionDeclaration, business_context: Dict[str, Any]) -> Dict[str, Any]:
    """Process completion declaration"""
    return await appendices_integration_service.process_completion_declaration(session_id, declaration, business_context)

async def generate_dynamic_prompts(session_id: str, business_context: Dict[str, Any], current_task: Optional[str] = None) -> List[DynamicPrompt]:
    """Generate dynamic prompts"""
    return await appendices_integration_service.generate_dynamic_prompts(session_id, business_context, current_task)
