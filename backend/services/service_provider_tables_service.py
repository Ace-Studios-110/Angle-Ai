from openai import AsyncOpenAI
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from services.rag_service import research_service_providers_rag
from services.specialized_agents_service import agents_manager

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ServiceProviderTableGenerator:
    """Generate comprehensive service provider tables with local providers"""
    
    def __init__(self):
        self.provider_categories = {
            "legal": {
                "name": "Legal Services",
                "subcategories": ["Business Formation", "Contract Law", "Intellectual Property", "Compliance"],
                "local_keywords": ["attorney", "lawyer", "law firm", "legal services"]
            },
            "financial": {
                "name": "Financial Services", 
                "subcategories": ["Accounting", "Tax Services", "Banking", "Financial Planning"],
                "local_keywords": ["cpa", "accountant", "bank", "financial advisor"]
            },
            "marketing": {
                "name": "Marketing Services",
                "subcategories": ["Digital Marketing", "Branding", "Content Creation", "Social Media"],
                "local_keywords": ["marketing agency", "digital marketing", "branding", "advertising"]
            },
            "operations": {
                "name": "Operations Services",
                "subcategories": ["Supply Chain", "Logistics", "Equipment", "Facilities"],
                "local_keywords": ["supplier", "vendor", "equipment", "facilities"]
            },
            "technology": {
                "name": "Technology Services",
                "subcategories": ["Software Development", "IT Support", "Web Development", "Cloud Services"],
                "local_keywords": ["software", "IT", "web development", "technology"]
            },
            "consulting": {
                "name": "Business Consulting",
                "subcategories": ["Strategy", "Management", "Industry Expertise", "Growth"],
                "local_keywords": ["consultant", "advisor", "strategist", "expert"]
            }
        }
    
    async def generate_service_provider_table(self, task_context: str, business_context: Dict[str, Any], location: str = None) -> Dict[str, Any]:
        """Generate a comprehensive service provider table for a specific task"""
        
        # Determine relevant service categories for the task
        relevant_categories = self._determine_relevant_categories(task_context)
        
        # Generate providers for each relevant category
        provider_tables = {}
        
        for category in relevant_categories:
            try:
                providers = await self._generate_category_providers(category, business_context, location)
                provider_tables[category] = providers
            except Exception as e:
                provider_tables[category] = {
                    "error": f"Failed to generate providers for {category}: {str(e)}",
                    "providers": []
                }
        
        # Generate comprehensive table with all providers
        comprehensive_table = await self._generate_comprehensive_table(provider_tables, task_context, business_context)
        
        return {
            "task_context": task_context,
            "business_context": business_context,
            "location": location,
            "relevant_categories": relevant_categories,
            "provider_tables": provider_tables,
            "comprehensive_table": comprehensive_table,
            "timestamp": datetime.now().isoformat()
        }
    
    def _determine_relevant_categories(self, task_context: str) -> List[str]:
        """Determine which service categories are relevant for the task"""
        
        task_lower = task_context.lower()
        relevant_categories = []
        
        # Legal keywords
        if any(keyword in task_lower for keyword in ['legal', 'compliance', 'license', 'permit', 'regulation', 'contract', 'incorporation']):
            relevant_categories.append("legal")
        
        # Financial keywords
        if any(keyword in task_lower for keyword in ['financial', 'accounting', 'tax', 'banking', 'funding', 'budget', 'revenue']):
            relevant_categories.append("financial")
        
        # Marketing keywords
        if any(keyword in task_lower for keyword in ['marketing', 'branding', 'advertising', 'social media', 'content', 'promotion']):
            relevant_categories.append("marketing")
        
        # Operations keywords
        if any(keyword in task_lower for keyword in ['operations', 'supply', 'equipment', 'facilities', 'logistics', 'production']):
            relevant_categories.append("operations")
        
        # Technology keywords
        if any(keyword in task_lower for keyword in ['technology', 'software', 'IT', 'website', 'digital', 'automation']):
            relevant_categories.append("technology")
        
        # Consulting keywords
        if any(keyword in task_lower for keyword in ['consulting', 'strategy', 'advice', 'guidance', 'expertise', 'planning']):
            relevant_categories.append("consulting")
        
        # If no specific keywords found, include all categories for comprehensive coverage
        if not relevant_categories:
            relevant_categories = list(self.provider_categories.keys())
        
        return relevant_categories
    
    async def _generate_category_providers(self, category: str, business_context: Dict[str, Any], location: str = None) -> Dict[str, Any]:
        """Generate providers for a specific category"""
        
        category_info = self.provider_categories[category]
        
        # Use RAG to research providers
        rag_results = await research_service_providers_rag(category, business_context, location)
        
        # Generate structured provider data
        providers = await self._create_structured_providers(category, category_info, business_context, location, rag_results)
        
        return {
            "category": category,
            "category_name": category_info["name"],
            "subcategories": category_info["subcategories"],
            "providers": providers,
            "rag_research": rag_results,
            "location": location
        }
    
    async def _create_structured_providers(self, category: str, category_info: Dict[str, Any], business_context: Dict[str, Any], location: str, rag_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create structured provider data"""
        
        # Generate providers using AI with RAG research
        provider_prompt = f"""
        Generate a comprehensive list of service providers for {category_info['name']} based on the following context:
        
        Business Context:
        - Industry: {business_context.get('industry', 'General Business')}
        - Location: {business_context.get('location', 'United States')}
        - Business Type: {business_context.get('business_type', 'Startup')}
        - Business Name: {business_context.get('business_name', 'Your Business')}
        
        Target Location: {location or business_context.get('location', 'United States')}
        
        Subcategories: {', '.join(category_info['subcategories'])}
        
        Research Data: {rag_results.get('recommendations', 'No specific research data available')}
        
        Generate at least 5 providers with the following structure for each:
        1. Name: Specific company/service name
        2. Type: Type of service (e.g., "Online Service", "Local Professional", "National Firm")
        3. Local: Boolean indicating if they serve the target location
        4. Description: Detailed description of services offered
        5. Key Considerations: Important factors to consider when choosing this provider
        6. Estimated Cost: Cost range or pricing model
        7. Contact Method: How to reach them
        8. Specialties: Specific areas of expertise
        
        Ensure you include:
        - At least 2 local providers (marked as Local: true)
        - Mix of online and offline services
        - Different price points and service levels
        - Providers suitable for startups/small businesses
        
        Format as JSON array of provider objects.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": provider_prompt}],
                temperature=0.4,
                max_tokens=2000
            )
            
            # Parse the response as JSON
            providers_text = response.choices[0].message.content
            
            # Extract JSON from the response
            import re
            json_match = re.search(r'\[.*\]', providers_text, re.DOTALL)
            if json_match:
                providers = json.loads(json_match.group())
            else:
                # Fallback: create providers from text
                providers = self._parse_providers_from_text(providers_text, category_info)
            
            # Ensure we have the required structure
            structured_providers = []
            for provider in providers:
                structured_provider = {
                    "name": provider.get("name", "Provider Name"),
                    "type": provider.get("type", "Service Provider"),
                    "local": provider.get("local", False),
                    "description": provider.get("description", "Service description"),
                    "key_considerations": provider.get("key_considerations", "Considerations"),
                    "estimated_cost": provider.get("estimated_cost", "Contact for pricing"),
                    "contact_method": provider.get("contact_method", "Website or phone"),
                    "specialties": provider.get("specialties", "General services")
                }
                structured_providers.append(structured_provider)
            
            return structured_providers
            
        except Exception as e:
            # Fallback: generate basic providers
            return self._generate_fallback_providers(category, category_info, business_context, location)
    
    def _parse_providers_from_text(self, text: str, category_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse providers from text response"""
        
        providers = []
        lines = text.split('\n')
        
        current_provider = {}
        for line in lines:
            line = line.strip()
            if line.startswith('Name:'):
                if current_provider:
                    providers.append(current_provider)
                current_provider = {"name": line.replace('Name:', '').strip()}
            elif line.startswith('Type:'):
                current_provider["type"] = line.replace('Type:', '').strip()
            elif line.startswith('Local:'):
                current_provider["local"] = 'true' in line.lower()
            elif line.startswith('Description:'):
                current_provider["description"] = line.replace('Description:', '').strip()
            elif line.startswith('Key Considerations:'):
                current_provider["key_considerations"] = line.replace('Key Considerations:', '').strip()
            elif line.startswith('Estimated Cost:'):
                current_provider["estimated_cost"] = line.replace('Estimated Cost:', '').strip()
            elif line.startswith('Contact Method:'):
                current_provider["contact_method"] = line.replace('Contact Method:', '').strip()
            elif line.startswith('Specialties:'):
                current_provider["specialties"] = line.replace('Specialties:', '').strip()
        
        if current_provider:
            providers.append(current_provider)
        
        return providers
    
    def _generate_fallback_providers(self, category: str, category_info: Dict[str, Any], business_context: Dict[str, Any], location: str) -> List[Dict[str, Any]]:
        """Generate fallback providers when AI generation fails"""
        
        fallback_providers = {
            "legal": [
                {
                    "name": "Local Business Attorney",
                    "type": "Legal Professional",
                    "local": True,
                    "description": f"Local attorney specializing in {business_context.get('industry', 'business')} law and business formation",
                    "key_considerations": "Industry experience, local knowledge, cost structure",
                    "estimated_cost": "$200-500/hour",
                    "contact_method": "Local bar association or referrals",
                    "specialties": "Business formation, contracts, compliance"
                },
                {
                    "name": "LegalZoom",
                    "type": "Online Service",
                    "local": False,
                    "description": "Online legal document preparation and business formation services",
                    "key_considerations": "Cost-effective, standardized, limited customization",
                    "estimated_cost": "$99-399",
                    "contact_method": "Online platform",
                    "specialties": "Business formation, document preparation"
                }
            ],
            "financial": [
                {
                    "name": "Local CPA Firm",
                    "type": "Accounting Professional",
                    "local": True,
                    "description": f"Certified Public Accountant specializing in {business_context.get('industry', 'small business')} accounting",
                    "key_considerations": "Industry expertise, local tax knowledge, ongoing support",
                    "estimated_cost": "$150-300/hour",
                    "contact_method": "Local CPA directory or referrals",
                    "specialties": "Tax preparation, bookkeeping, financial planning"
                },
                {
                    "name": "QuickBooks ProAdvisor",
                    "type": "Online Service",
                    "local": False,
                    "description": "Certified QuickBooks professionals for accounting setup and training",
                    "key_considerations": "QuickBooks expertise, remote support, cost-effective",
                    "estimated_cost": "$50-150/hour",
                    "contact_method": "QuickBooks ProAdvisor directory",
                    "specialties": "QuickBooks setup, training, bookkeeping"
                }
            ],
            "marketing": [
                {
                    "name": "Local Marketing Agency",
                    "type": "Marketing Professional",
                    "local": True,
                    "description": f"Full-service marketing agency with {business_context.get('industry', 'local business')} experience",
                    "key_considerations": "Local market knowledge, full-service capabilities, ongoing support",
                    "estimated_cost": "$2,000-10,000/month",
                    "contact_method": "Local business directory or referrals",
                    "specialties": "Digital marketing, branding, local SEO"
                },
                {
                    "name": "HubSpot Partner",
                    "type": "Online Service",
                    "local": False,
                    "description": "Certified HubSpot partners for inbound marketing and CRM setup",
                    "key_considerations": "HubSpot expertise, inbound marketing, scalable solutions",
                    "estimated_cost": "$1,000-5,000/month",
                    "contact_method": "HubSpot Partner directory",
                    "specialties": "Inbound marketing, CRM, marketing automation"
                }
            ]
        }
        
        return fallback_providers.get(category, [
            {
                "name": f"Local {category_info['name']} Provider",
                "type": "Local Professional",
                "local": True,
                "description": f"Local provider specializing in {category_info['name']}",
                "key_considerations": "Local expertise, personalized service",
                "estimated_cost": "Contact for pricing",
                "contact_method": "Local directory or referrals",
                "specialties": "General services"
            }
        ])
    
    async def _generate_comprehensive_table(self, provider_tables: Dict[str, Any], task_context: str, business_context: Dict[str, Any]) -> str:
        """Generate a comprehensive service provider table"""
        
        # Create comprehensive table using AI
        table_prompt = f"""
        Create a comprehensive service provider table for the following task:
        
        Task Context: {task_context}
        Business Context: {business_context}
        
        Provider Data: {json.dumps(provider_tables, indent=2)}
        
        Generate a well-formatted table that includes:
        1. Provider Name
        2. Type (Local/Online/National)
        3. Description
        4. Key Considerations
        5. Estimated Cost
        6. Contact Method
        7. Specialties
        
        Format as a markdown table with clear headers and organized by service category.
        Include a summary of recommendations and selection criteria.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": table_prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Comprehensive table generation failed: {str(e)}"
    
    async def get_task_specific_providers(self, task_id: str, task_description: str, business_context: Dict[str, Any], location: str = None) -> Dict[str, Any]:
        """Get providers specific to a particular implementation task"""
        
        # Use specialized agents to determine the best providers for this task
        agent_guidance = await agents_manager.get_multi_agent_guidance(
            f"Recommend service providers for: {task_description}",
            business_context,
            []
        )
        
        # Generate provider table based on agent recommendations
        provider_table = await self.generate_service_provider_table(
            task_description,
            business_context,
            location
        )
        
        # Combine agent guidance with provider recommendations
        enhanced_table = await self._enhance_table_with_agent_guidance(
            provider_table,
            agent_guidance,
            task_description
        )
        
        return {
            "task_id": task_id,
            "task_description": task_description,
            "agent_guidance": agent_guidance,
            "provider_table": enhanced_table,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _enhance_table_with_agent_guidance(self, provider_table: Dict[str, Any], agent_guidance: Dict[str, Any], task_description: str) -> Dict[str, Any]:
        """Enhance provider table with agent guidance"""
        
        enhancement_prompt = f"""
        Enhance the following service provider table with expert guidance:
        
        Task Description: {task_description}
        
        Provider Table: {json.dumps(provider_table, indent=2)}
        
        Agent Guidance: {json.dumps(agent_guidance, indent=2)}
        
        Enhance the table by:
        1. Adding expert recommendations and insights
        2. Including selection criteria based on agent expertise
        3. Adding risk assessments and considerations
        4. Providing decision-making frameworks
        5. Including questions to ask providers
        
        Format as an enhanced provider table with expert insights.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": enhancement_prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            return {
                "original_table": provider_table,
                "enhanced_table": response.choices[0].message.content,
                "agent_insights": agent_guidance,
                "enhancement_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "original_table": provider_table,
                "enhanced_table": f"Enhancement failed: {str(e)}",
                "agent_insights": agent_guidance
            }

# Global instance
provider_table_generator = ServiceProviderTableGenerator()

# Convenience functions
async def generate_provider_table(task_context: str, business_context: Dict[str, Any], location: str = None) -> Dict[str, Any]:
    """Generate a service provider table for a specific task"""
    return await provider_table_generator.generate_service_provider_table(task_context, business_context, location)

async def get_task_providers(task_id: str, task_description: str, business_context: Dict[str, Any], location: str = None) -> Dict[str, Any]:
    """Get providers for a specific implementation task"""
    return await provider_table_generator.get_task_specific_providers(task_id, task_description, business_context, location)
