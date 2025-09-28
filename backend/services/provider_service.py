from openai import AsyncOpenAI
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from services.angel_service import conduct_web_search

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Provider categories and templates
PROVIDER_CATEGORIES = {
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

async def generate_provider_table(task_type: str, industry: str, location: str, business_context: Dict = None) -> List[Dict]:
    """Generate a provider table for a specific task with local and national providers"""
    
    try:
        # Conduct research for providers
        current_year = datetime.now().year
        previous_year = current_year - 1
        
        # Search for local and national providers
        local_providers_research = await conduct_web_search(f"site:yelp.com OR site:google.com {task_type} services {location} {industry} {previous_year}")
        national_providers_research = await conduct_web_search(f"best {task_type} services {industry} {previous_year}")
        industry_specific_research = await conduct_web_search(f"{industry} {task_type} providers {location} {previous_year}")
        
        # Generate provider recommendations using AI
        provider_prompt = f"""
        Based on the research data below, generate a provider table for {task_type} services in the {industry} industry located in {location}.
        
        Research Data:
        Local Providers: {local_providers_research}
        National Providers: {national_providers_research}
        Industry Specific: {industry_specific_research}
        
        Business Context: {json.dumps(business_context or {}, indent=2)}
        
        Generate a JSON array of 3-5 providers with the following structure:
        [
            {{
                "name": "Provider Name",
                "type": "Service Type (e.g., Online Service, Professional Service, Government)",
                "local": true/false,
                "description": "Brief description of services offered",
                "key_considerations": "Important factors to consider when choosing this provider",
                "contact_info": "How to contact them (website, phone, etc.)",
                "pricing": "General pricing information",
                "rating": "If available, quality rating or reputation"
            }}
        ]
        
        Requirements:
        - Include at least 1 local provider marked as "local": true
        - Include at least 1 national/online provider marked as "local": false  
        - Ensure providers are relevant to {task_type} and {industry}
        - Provide realistic and helpful descriptions
        - Include credible, well-known providers where possible
        - Mark local providers clearly with "local": true
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": provider_prompt}],
            temperature=0.3
        )
        
        provider_data = response.choices[0].message.content
        
        # Try to parse JSON response
        try:
            providers = json.loads(provider_data)
            return providers
        except json.JSONDecodeError:
            # If JSON parsing fails, return default providers
            return get_default_providers(task_type, industry, location)
            
    except Exception as e:
        print(f"Error generating provider table: {e}")
        return get_default_providers(task_type, industry, location)

def get_default_providers(task_type: str, industry: str, location: str) -> List[Dict]:
    """Fallback provider recommendations when AI generation fails"""
    
    default_providers = {
        "legal_formation": [
            {
                "name": "LegalZoom",
                "type": "Online Service",
                "local": False,
                "description": "Online legal document preparation and business formation services",
                "key_considerations": "Cost-effective, standardized process, good for simple formations",
                "contact_info": "www.legalzoom.com",
                "pricing": "$149-$349 depending on state and services",
                "rating": "4.5/5 stars"
            },
            {
                "name": "Local Business Attorney",
                "type": "Legal Professional",
                "local": True,
                "description": "Personalized legal advice and business formation assistance",
                "key_considerations": "Industry-specific expertise, personalized service, higher cost",
                "contact_info": "Search local business attorneys in your area",
                "pricing": "$200-$500 per hour",
                "rating": "Varies by attorney"
            },
            {
                "name": "SCORE Business Mentor",
                "type": "Free Consultation",
                "local": True,
                "description": "Volunteer business mentors offering free guidance",
                "key_considerations": "Free service, experienced mentors, limited availability",
                "contact_info": "www.score.org",
                "pricing": "Free",
                "rating": "Highly recommended"
            }
        ],
        "banking": [
            {
                "name": "Chase Business",
                "type": "Traditional Bank",
                "local": True,
                "description": "Full-service business banking with extensive branch network",
                "key_considerations": "Convenient locations, comprehensive services, monthly fees",
                "contact_info": "www.chase.com/business",
                "pricing": "$15-$95 monthly depending on account type",
                "rating": "4.2/5 stars"
            },
            {
                "name": "Capital One Spark",
                "type": "Online Banking",
                "local": False,
                "description": "Digital-first business banking with no monthly fees",
                "key_considerations": "No monthly fees, online-only, good for tech-savvy businesses",
                "contact_info": "www.capitalone.com/spark",
                "pricing": "No monthly fees",
                "rating": "4.3/5 stars"
            },
            {
                "name": "Local Credit Union",
                "type": "Credit Union",
                "local": True,
                "description": "Community-focused banking with personalized service",
                "key_considerations": "Lower fees, community focus, limited services",
                "contact_info": "Search local credit unions",
                "pricing": "Varies, typically lower than banks",
                "rating": "High customer satisfaction"
            }
        ],
        "accounting": [
            {
                "name": "QuickBooks",
                "type": "Software Platform",
                "local": False,
                "description": "Industry-leading accounting and bookkeeping software",
                "key_considerations": "Comprehensive features, learning curve, integrates with many tools",
                "contact_info": "www.quickbooks.intuit.com",
                "pricing": "$15-$200/month depending on plan",
                "rating": "4.4/5 stars"
            },
            {
                "name": "Local CPA Firm",
                "type": "Professional Service",
                "local": True,
                "description": "Certified public accountants offering bookkeeping and tax services",
                "key_considerations": "Expert guidance, compliance assurance, ongoing support",
                "contact_info": "Search local CPA firms",
                "pricing": "$100-$300/hour",
                "rating": "Professional expertise"
            },
            {
                "name": "Wave",
                "type": "Software Platform",
                "local": False,
                "description": "Free accounting software for small businesses",
                "key_considerations": "Free basic features, good for simple businesses, limited support",
                "contact_info": "www.waveapps.com",
                "pricing": "Free basic plan",
                "rating": "4.2/5 stars"
            }
        ]
    }
    
    # Return appropriate providers based on task type
    task_key = task_type.lower().replace(" ", "_")
    if task_key in default_providers:
        return default_providers[task_key]
    else:
        # Generic fallback
        return [
            {
                "name": "Local Service Provider",
                "type": "Professional Service",
                "local": True,
                "description": f"Local {task_type} services in {location}",
                "key_considerations": "Local expertise, personalized service, convenient location",
                "contact_info": "Search local directories",
                "pricing": "Contact for pricing",
                "rating": "Varies by provider"
            },
            {
                "name": "National Online Service",
                "type": "Online Service",
                "local": False,
                "description": f"Online {task_type} services",
                "key_considerations": "Convenient, cost-effective, standardized process",
                "contact_info": "Search online service providers",
                "pricing": "Varies by service",
                "rating": "Varies by provider"
            }
        ]

async def get_provider_recommendations(task_id: str, industry: str, location: str, business_context: Dict = None) -> Dict:
    """Get provider recommendations for a specific implementation task"""
    
    # Map task IDs to provider categories
    task_mapping = {
        "LEGAL_01": "legal_formation",
        "LEGAL_02": "legal_formation", 
        "LEGAL_03": "legal_formation",
        "FINANCIAL_01": "banking",
        "FINANCIAL_02": "accounting",
        "FINANCIAL_03": "accounting",
        "OPERATIONS_01": "operational_services",
        "OPERATIONS_02": "operational_services",
        "MARKETING_01": "marketing_services",
        "MARKETING_02": "marketing_services",
        "LAUNCH_01": "marketing_services",
        "LAUNCH_02": "operational_services"
    }
    
    task_type = task_mapping.get(task_id, "general_services")
    providers = await generate_provider_table(task_type, industry, location, business_context)
    
    return {
        "task_id": task_id,
        "task_type": task_type,
        "industry": industry,
        "location": location,
        "providers": providers,
        "generated_at": datetime.now().isoformat(),
        "research_conducted": True
    }

