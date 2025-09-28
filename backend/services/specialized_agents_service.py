from openai import AsyncOpenAI
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from services.angel_service import conduct_web_search

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class SpecializedAgent:
    """Base class for specialized agents"""
    
    def __init__(self, name: str, expertise: str, research_sources: List[str]):
        self.name = name
        self.expertise = expertise
        self.research_sources = research_sources
    
    async def conduct_research(self, query: str, business_context: Dict[str, Any]) -> str:
        """Conduct research using specialized sources"""
        try:
            # Combine query with business context for more targeted research
            enhanced_query = f"{query} {business_context.get('industry', '')} {business_context.get('location', '')}"
            
            # Use multiple research sources
            research_results = []
            for source in self.research_sources:
                search_query = f"site:{source} {enhanced_query}"
                result = await conduct_web_search(search_query)
                if result and "unable to conduct web research" not in result:
                    research_results.append(f"Source: {source}\n{result}")
            
            return "\n\n".join(research_results) if research_results else "No specific research results found."
        except Exception as e:
            print(f"Research error for {self.name}: {e}")
            return "Research temporarily unavailable."
    
    async def provide_expert_guidance(self, question: str, business_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
        """Provide expert guidance based on specialization"""
        raise NotImplementedError("Subclasses must implement provide_expert_guidance")

class LegalComplianceAgent(SpecializedAgent):
    """Legal & Compliance Specialist"""
    
    def __init__(self):
        super().__init__(
            name="Legal & Compliance Specialist",
            expertise="Business formation, licensing, permits, and compliance at all levels",
            research_sources=["sba.gov", "sec.gov", "irs.gov", "law.com", "martindale.com"]
        )
    
    async def provide_expert_guidance(self, question: str, business_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
        """Provide legal and compliance guidance"""
        
        # Conduct specialized research
        research_query = f"business formation legal requirements {business_context.get('industry', '')} {business_context.get('location', '')}"
        research_results = await self.conduct_research(research_query, business_context)
        
        # Generate expert guidance
        guidance_prompt = f"""
        You are a Legal & Compliance Specialist with expertise in business formation, licensing, permits, and compliance.
        
        Business Context:
        - Industry: {business_context.get('industry', 'General Business')}
        - Location: {business_context.get('location', 'United States')}
        - Business Type: {business_context.get('business_type', 'Startup')}
        
        Research Results:
        {research_results}
        
        Question/Task: {question}
        
        Provide comprehensive legal guidance including:
        1. Required business structure options (LLC, Corporation, Partnership, etc.)
        2. Licensing and permit requirements
        3. Compliance obligations
        4. Risk mitigation strategies
        5. Timeline and costs
        6. Local service provider recommendations
        
        Format your response as structured guidance with clear action items.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": guidance_prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            return {
                "agent": self.name,
                "expertise": self.expertise,
                "guidance": response.choices[0].message.content,
                "research_sources": self.research_sources,
                "research_results": research_results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "agent": self.name,
                "error": f"Failed to generate guidance: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

class FinancialPlanningAgent(SpecializedAgent):
    """Financial Planning & Funding Specialist"""
    
    def __init__(self):
        super().__init__(
            name="Financial Planning & Funding Specialist",
            expertise="Budgeting, forecasting, funding strategies, and accounting best practices",
            research_sources=["forbes.com", "hbr.org", "bloomberg.com", "wsj.com", "cpa.com"]
        )
    
    async def provide_expert_guidance(self, question: str, business_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
        """Provide financial planning and funding guidance"""
        
        # Conduct specialized research
        research_query = f"funding strategies financial planning {business_context.get('industry', '')} startup"
        research_results = await self.conduct_research(research_query, business_context)
        
        # Generate expert guidance
        guidance_prompt = f"""
        You are a Financial Planning & Funding Specialist with expertise in budgeting, forecasting, funding strategies, and accounting best practices.
        
        Business Context:
        - Industry: {business_context.get('industry', 'General Business')}
        - Location: {business_context.get('location', 'United States')}
        - Business Type: {business_context.get('business_type', 'Startup')}
        
        Research Results:
        {research_results}
        
        Question/Task: {question}
        
        Provide comprehensive financial guidance including:
        1. Funding options and strategies
        2. Budget planning and cash flow management
        3. Financial projections and forecasting
        4. Accounting system recommendations
        5. Tax planning considerations
        6. Financial service provider recommendations
        
        Format your response as structured guidance with clear action items and financial metrics.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": guidance_prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            return {
                "agent": self.name,
                "expertise": self.expertise,
                "guidance": response.choices[0].message.content,
                "research_sources": self.research_sources,
                "research_results": research_results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "agent": self.name,
                "error": f"Failed to generate guidance: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

class ProductOperationsAgent(SpecializedAgent):
    """Product & Operations Specialist"""
    
    def __init__(self):
        super().__init__(
            name="Product & Operations Specialist",
            expertise="Supply chain management, equipment procurement, operational efficiency, and workflow automation",
            research_sources=["alibaba.com", "amazon.com", "linkedin.com", "clutch.co", "gartner.com"]
        )
    
    async def provide_expert_guidance(self, question: str, business_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
        """Provide product and operations guidance"""
        
        # Conduct specialized research
        research_query = f"supply chain operations {business_context.get('industry', '')} equipment procurement"
        research_results = await self.conduct_research(research_query, business_context)
        
        # Generate expert guidance
        guidance_prompt = f"""
        You are a Product & Operations Specialist with expertise in supply chain management, equipment procurement, operational efficiency, and workflow automation.
        
        Business Context:
        - Industry: {business_context.get('industry', 'General Business')}
        - Location: {business_context.get('location', 'United States')}
        - Business Type: {business_context.get('business_type', 'Startup')}
        
        Research Results:
        {research_results}
        
        Question/Task: {question}
        
        Provide comprehensive operations guidance including:
        1. Supply chain setup and vendor relationships
        2. Equipment and technology procurement
        3. Operational processes and workflows
        4. Quality control systems
        5. Inventory management strategies
        6. Operational service provider recommendations
        
        Format your response as structured guidance with clear action items and operational metrics.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": guidance_prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            return {
                "agent": self.name,
                "expertise": self.expertise,
                "guidance": response.choices[0].message.content,
                "research_sources": self.research_sources,
                "research_results": research_results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "agent": self.name,
                "error": f"Failed to generate guidance: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

class MarketingCustomerAgent(SpecializedAgent):
    """Marketing & Customer Acquisition Specialist"""
    
    def __init__(self):
        super().__init__(
            name="Marketing & Customer Acquisition Specialist",
            expertise="Brand positioning, digital and traditional marketing, customer engagement, and competitive analysis",
            research_sources=["hubspot.com", "marketingland.com", "socialmediaexaminer.com", "adweek.com", "forbes.com"]
        )
    
    async def provide_expert_guidance(self, question: str, business_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
        """Provide marketing and customer acquisition guidance"""
        
        # Conduct specialized research
        research_query = f"marketing strategy customer acquisition {business_context.get('industry', '')} digital marketing"
        research_results = await self.conduct_research(research_query, business_context)
        
        # Generate expert guidance
        guidance_prompt = f"""
        You are a Marketing & Customer Acquisition Specialist with expertise in brand positioning, digital and traditional marketing, customer engagement, and competitive analysis.
        
        Business Context:
        - Industry: {business_context.get('industry', 'General Business')}
        - Location: {business_context.get('location', 'United States')}
        - Business Type: {business_context.get('business_type', 'Startup')}
        
        Research Results:
        {research_results}
        
        Question/Task: {question}
        
        Provide comprehensive marketing guidance including:
        1. Brand positioning and messaging strategy
        2. Digital and traditional marketing channels
        3. Customer acquisition strategies
        4. Competitive analysis and differentiation
        5. Marketing budget allocation
        6. Marketing service provider recommendations
        
        Format your response as structured guidance with clear action items and marketing metrics.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": guidance_prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            return {
                "agent": self.name,
                "expertise": self.expertise,
                "guidance": response.choices[0].message.content,
                "research_sources": self.research_sources,
                "research_results": research_results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "agent": self.name,
                "error": f"Failed to generate guidance: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

class BusinessStrategyAgent(SpecializedAgent):
    """Business Model & Strategy Specialist"""
    
    def __init__(self):
        super().__init__(
            name="Business Model & Strategy Specialist",
            expertise="Market research, competitive differentiation, revenue model optimization, and strategic planning",
            research_sources=["hbr.org", "mckinsey.com", "bain.com", "deloitte.com", "pwc.com"]
        )
    
    async def provide_expert_guidance(self, question: str, business_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
        """Provide business strategy guidance"""
        
        # Conduct specialized research
        research_query = f"business model strategy market research {business_context.get('industry', '')} competitive analysis"
        research_results = await self.conduct_research(research_query, business_context)
        
        # Generate expert guidance
        guidance_prompt = f"""
        You are a Business Model & Strategy Specialist with expertise in market research, competitive differentiation, revenue model optimization, and strategic planning.
        
        Business Context:
        - Industry: {business_context.get('industry', 'General Business')}
        - Location: {business_context.get('location', 'United States')}
        - Business Type: {business_context.get('business_type', 'Startup')}
        
        Research Results:
        {research_results}
        
        Question/Task: {question}
        
        Provide comprehensive strategy guidance including:
        1. Market research and analysis
        2. Competitive differentiation strategies
        3. Revenue model optimization
        4. Strategic planning frameworks
        5. Growth and scaling strategies
        6. Strategic consulting service provider recommendations
        
        Format your response as structured guidance with clear action items and strategic frameworks.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": guidance_prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            return {
                "agent": self.name,
                "expertise": self.expertise,
                "guidance": response.choices[0].message.content,
                "research_sources": self.research_sources,
                "research_results": research_results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "agent": self.name,
                "error": f"Failed to generate guidance: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

class RoadmapExecutionAgent(SpecializedAgent):
    """Roadmap Execution & Scaling Specialist"""
    
    def __init__(self):
        super().__init__(
            name="Roadmap Execution & Scaling Specialist",
            expertise="Milestone planning, task sequencing, team building, scaling strategies, and long-term sustainability",
            research_sources=["scaledagileframework.com", "atlassian.com", "monday.com", "asana.com", "trello.com"]
        )
    
    async def provide_expert_guidance(self, question: str, business_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
        """Provide roadmap execution and scaling guidance"""
        
        # Conduct specialized research
        research_query = f"roadmap execution scaling strategies {business_context.get('industry', '')} project management"
        research_results = await self.conduct_research(research_query, business_context)
        
        # Generate expert guidance
        guidance_prompt = f"""
        You are a Roadmap Execution & Scaling Specialist with expertise in milestone planning, task sequencing, team building, scaling strategies, and long-term sustainability.
        
        Business Context:
        - Industry: {business_context.get('industry', 'General Business')}
        - Location: {business_context.get('location', 'United States')}
        - Business Type: {business_context.get('business_type', 'Startup')}
        
        Research Results:
        {research_results}
        
        Question/Task: {question}
        
        Provide comprehensive execution guidance including:
        1. Milestone planning and task sequencing
        2. Team building and organizational structure
        3. Scaling strategies and growth planning
        4. Project management methodologies
        5. Performance tracking and KPIs
        6. Execution service provider recommendations
        
        Format your response as structured guidance with clear action items and execution metrics.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": guidance_prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            return {
                "agent": self.name,
                "expertise": self.expertise,
                "guidance": response.choices[0].message.content,
                "research_sources": self.research_sources,
                "research_results": research_results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "agent": self.name,
                "error": f"Failed to generate guidance: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

class SpecializedAgentsManager:
    """Manager for all specialized agents"""
    
    def __init__(self):
        self.agents = {
            "legal": LegalComplianceAgent(),
            "financial": FinancialPlanningAgent(),
            "operations": ProductOperationsAgent(),
            "marketing": MarketingCustomerAgent(),
            "strategy": BusinessStrategyAgent(),
            "execution": RoadmapExecutionAgent()
        }
    
    async def get_agent_guidance(self, agent_type: str, question: str, business_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
        """Get guidance from a specific agent"""
        
        if agent_type not in self.agents:
            return {
                "error": f"Unknown agent type: {agent_type}",
                "available_agents": list(self.agents.keys())
            }
        
        agent = self.agents[agent_type]
        return await agent.provide_expert_guidance(question, business_context, conversation_history)
    
    async def get_multi_agent_guidance(self, question: str, business_context: Dict[str, Any], conversation_history: List[Dict], relevant_agents: List[str] = None) -> Dict[str, Any]:
        """Get guidance from multiple relevant agents"""
        
        if relevant_agents is None:
            # Determine relevant agents based on question content
            relevant_agents = self._determine_relevant_agents(question, business_context)
        
        guidance_results = {}
        
        for agent_type in relevant_agents:
            if agent_type in self.agents:
                try:
                    guidance = await self.get_agent_guidance(agent_type, question, business_context, conversation_history)
                    guidance_results[agent_type] = guidance
                except Exception as e:
                    guidance_results[agent_type] = {
                        "error": f"Failed to get guidance from {agent_type}: {str(e)}"
                    }
        
        return {
            "multi_agent_guidance": guidance_results,
            "relevant_agents": relevant_agents,
            "timestamp": datetime.now().isoformat()
        }
    
    def _determine_relevant_agents(self, question: str, business_context: Dict[str, Any]) -> List[str]:
        """Determine which agents are relevant based on question content"""
        
        question_lower = question.lower()
        relevant_agents = []
        
        # Legal keywords
        if any(keyword in question_lower for keyword in ['legal', 'compliance', 'license', 'permit', 'regulation', 'structure', 'incorporation']):
            relevant_agents.append("legal")
        
        # Financial keywords
        if any(keyword in question_lower for keyword in ['financial', 'funding', 'budget', 'accounting', 'tax', 'revenue', 'cost', 'investment']):
            relevant_agents.append("financial")
        
        # Operations keywords
        if any(keyword in question_lower for keyword in ['operations', 'supply', 'equipment', 'process', 'workflow', 'production', 'inventory']):
            relevant_agents.append("operations")
        
        # Marketing keywords
        if any(keyword in question_lower for keyword in ['marketing', 'brand', 'customer', 'sales', 'advertising', 'promotion', 'social media']):
            relevant_agents.append("marketing")
        
        # Strategy keywords
        if any(keyword in question_lower for keyword in ['strategy', 'market research', 'competitive', 'business model', 'differentiation']):
            relevant_agents.append("strategy")
        
        # Execution keywords
        if any(keyword in question_lower for keyword in ['execution', 'implementation', 'roadmap', 'milestone', 'scaling', 'team', 'project']):
            relevant_agents.append("execution")
        
        # If no specific keywords found, include all agents for comprehensive guidance
        if not relevant_agents:
            relevant_agents = list(self.agents.keys())
        
        return relevant_agents
    
    def get_agent_info(self) -> Dict[str, Dict[str, str]]:
        """Get information about all available agents"""
        
        agent_info = {}
        for agent_type, agent in self.agents.items():
            agent_info[agent_type] = {
                "name": agent.name,
                "expertise": agent.expertise,
                "research_sources": agent.research_sources
            }
        
        return agent_info

# Global instance
agents_manager = SpecializedAgentsManager()

# Convenience functions
async def get_legal_guidance(question: str, business_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
    """Get legal and compliance guidance"""
    return await agents_manager.get_agent_guidance("legal", question, business_context, conversation_history)

async def get_financial_guidance(question: str, business_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
    """Get financial planning guidance"""
    return await agents_manager.get_agent_guidance("financial", question, business_context, conversation_history)

async def get_operations_guidance(question: str, business_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
    """Get operations guidance"""
    return await agents_manager.get_agent_guidance("operations", question, business_context, conversation_history)

async def get_marketing_guidance(question: str, business_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
    """Get marketing guidance"""
    return await agents_manager.get_agent_guidance("marketing", question, business_context, conversation_history)

async def get_strategy_guidance(question: str, business_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
    """Get strategy guidance"""
    return await agents_manager.get_agent_guidance("strategy", question, business_context, conversation_history)

async def get_execution_guidance(question: str, business_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
    """Get execution guidance"""
    return await agents_manager.get_agent_guidance("execution", question, business_context, conversation_history)

async def get_comprehensive_guidance(question: str, business_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
    """Get comprehensive guidance from all relevant agents"""
    return await agents_manager.get_multi_agent_guidance(question, business_context, conversation_history)
