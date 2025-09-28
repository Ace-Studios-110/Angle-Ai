from openai import AsyncOpenAI
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from services.specialized_agents_service import agents_manager
from services.rag_service import conduct_rag_research, validate_with_rag, generate_rag_insights
from services.service_provider_tables_service import generate_provider_table, get_task_providers

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ImplementationTaskManager:
    """Manages implementation tasks with RAG-powered guidance and service providers"""
    
    def __init__(self):
        self.task_phases = {
            "legal_formation": {
                "name": "Legal Formation & Compliance",
                "tasks": [
                    "business_structure_selection",
                    "business_registration",
                    "tax_id_application",
                    "permits_licenses",
                    "insurance_requirements"
                ]
            },
            "financial_setup": {
                "name": "Financial Planning & Setup",
                "tasks": [
                    "business_bank_account",
                    "accounting_system",
                    "budget_planning",
                    "funding_strategy",
                    "financial_tracking"
                ]
            },
            "operations_development": {
                "name": "Product & Operations Development",
                "tasks": [
                    "supply_chain_setup",
                    "equipment_procurement",
                    "operational_processes",
                    "quality_control",
                    "inventory_management"
                ]
            },
            "marketing_sales": {
                "name": "Marketing & Sales Strategy",
                "tasks": [
                    "brand_development",
                    "marketing_strategy",
                    "sales_process",
                    "customer_acquisition",
                    "digital_presence"
                ]
            },
            "launch_scaling": {
                "name": "Full Launch & Scaling",
                "tasks": [
                    "go_to_market",
                    "team_building",
                    "performance_monitoring",
                    "growth_strategies",
                    "customer_feedback"
                ]
            }
        }
    
    async def get_next_implementation_task(self, session_data: Dict[str, Any], completed_tasks: List[str]) -> Dict[str, Any]:
        """Get the next implementation task based on progress"""
        
        # Determine current phase and next task
        current_phase, next_task_id = self._determine_next_task(completed_tasks)
        
        if not next_task_id:
            return {"status": "completed", "message": "All implementation tasks completed"}
        
        # Generate task details with RAG research
        task_details = await self._generate_task_details(next_task_id, session_data)
        
        # Get service providers for this task
        service_providers = await self._get_task_service_providers(next_task_id, session_data)
        
        # Generate mentor insights
        mentor_insights = await self._generate_mentor_insights(next_task_id, session_data)
        
        return {
            "task_id": next_task_id,
            "phase": current_phase,
            "task_details": task_details,
            "service_providers": service_providers,
            "mentor_insights": mentor_insights,
            "angel_actions": self._get_angel_actions(next_task_id),
            "estimated_time": self._get_estimated_time(next_task_id),
            "priority": self._get_priority(next_task_id)
        }
    
    def _determine_next_task(self, completed_tasks: List[str]) -> tuple[str, str]:
        """Determine the next task based on completed tasks"""
        
        for phase_key, phase_data in self.task_phases.items():
            for task_id in phase_data["tasks"]:
                if task_id not in completed_tasks:
                    return phase_key, task_id
        
        return None, None
