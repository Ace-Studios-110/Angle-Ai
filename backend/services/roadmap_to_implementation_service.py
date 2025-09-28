from openai import AsyncOpenAI
import os
import json
import random
from datetime import datetime
from typing import Dict, List, Optional
from utils.constant import ANGEL_SYSTEM_PROMPT

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Motivational quotes for business implementation
MOTIVATIONAL_QUOTES = [
    {
        "quote": "Success is not final; failure is not fatal: it is the courage to continue that counts.",
        "author": "Winston Churchill",
        "category": "Persistence"
    },
    {
        "quote": "The way to get started is to quit talking and begin doing.",
        "author": "Walt Disney",
        "category": "Action"
    },
    {
        "quote": "Innovation distinguishes between a leader and a follower.",
        "author": "Steve Jobs",
        "category": "Innovation"
    },
    {
        "quote": "The future belongs to those who believe in the beauty of their dreams.",
        "author": "Eleanor Roosevelt",
        "category": "Vision"
    },
    {
        "quote": "Don't be afraid to give up the good to go for the great.",
        "author": "John D. Rockefeller",
        "category": "Ambition"
    },
    {
        "quote": "The only way to do great work is to love what you do.",
        "author": "Steve Jobs",
        "category": "Passion"
    },
    {
        "quote": "Success usually comes to those who are too busy to be looking for it.",
        "author": "Henry David Thoreau",
        "category": "Focus"
    },
    {
        "quote": "Your time is limited, don't waste it living someone else's life.",
        "author": "Steve Jobs",
        "category": "Authenticity"
    }
]

# Service provider categories with sample providers
SERVICE_PROVIDER_CATEGORIES = {
    "legal": [
        {
            "name": "LegalZoom",
            "type": "Online Legal Services",
            "description": "Comprehensive online legal services for business formation",
            "local": False
        },
        {
            "name": "Rocket Lawyer",
            "type": "Online Legal Platform", 
            "description": "Affordable legal services and document templates",
            "local": False
        }
    ],
    "financial": [
        {
            "name": "QuickBooks",
            "type": "Accounting Software",
            "description": "Leading accounting software for small businesses",
            "local": False
        },
        {
            "name": "Xero",
            "type": "Cloud Accounting",
            "description": "Modern cloud-based accounting platform",
            "local": False
        }
    ],
    "marketing": [
        {
            "name": "HubSpot",
            "type": "Marketing Platform",
            "description": "All-in-one marketing, sales, and service platform",
            "local": False
        },
        {
            "name": "Mailchimp",
            "type": "Email Marketing",
            "description": "Email marketing and automation platform",
            "local": False
        }
    ],
    "technology": [
        {
            "name": "Shopify",
            "type": "E-commerce Platform",
            "description": "Complete e-commerce solution for online stores",
            "local": False
        },
        {
            "name": "Squarespace",
            "type": "Website Builder",
            "description": "Website building and hosting platform",
            "local": False
        }
    ]
}

async def get_motivational_quote(business_context: Dict) -> Dict:
    """Get a motivational quote tailored to the business context"""
    
    # Select a relevant quote based on business context
    industry = business_context.get('industry', '').lower()
    business_type = business_context.get('business_type', '').lower()
    
    # Filter quotes based on business context
    relevant_quotes = MOTIVATIONAL_QUOTES.copy()
    
    if 'tech' in industry or 'technology' in industry:
        relevant_quotes.extend([
            q for q in MOTIVATIONAL_QUOTES 
            if q['category'] in ['Innovation', 'Vision']
        ])
    elif 'service' in business_type:
        relevant_quotes.extend([
            q for q in MOTIVATIONAL_QUOTES 
            if q['category'] in ['Passion', 'Authenticity']
        ])
    elif 'startup' in business_type:
        relevant_quotes.extend([
            q for q in MOTIVATIONAL_QUOTES 
            if q['category'] in ['Action', 'Ambition']
        ])
    
    # Return a random quote from the relevant ones
    return random.choice(relevant_quotes)

async def get_service_provider_preview(business_context: Dict) -> List[Dict]:
    """Get a preview of service providers relevant to the business context"""
    
    industry = business_context.get('industry', '').lower()
    business_type = business_context.get('business_type', '').lower()
    location = business_context.get('location', 'United States')
    
    providers = []
    
    # Always include legal and financial providers
    providers.extend(SERVICE_PROVIDER_CATEGORIES['legal'])
    providers.extend(SERVICE_PROVIDER_CATEGORIES['financial'])
    
    # Add industry-specific providers
    if 'tech' in industry or 'software' in industry:
        providers.extend(SERVICE_PROVIDER_CATEGORIES['technology'])
    elif 'retail' in industry or 'ecommerce' in industry:
        providers.extend(SERVICE_PROVIDER_CATEGORIES['technology'])
    elif 'service' in business_type or 'consulting' in business_type:
        providers.extend(SERVICE_PROVIDER_CATEGORIES['marketing'])
    
    # Add local providers (marked as local)
    local_providers = []
    if location != 'United States':
        local_providers.append({
            "name": f"Local Business Attorney - {location}",
            "type": "Local Legal Services",
            "description": f"Personalized legal guidance for business formation in {location}",
            "local": True
        })
        local_providers.append({
            "name": f"Local CPA - {location}",
            "type": "Local Accounting Services", 
            "description": f"Personalized accounting and tax services in {location}",
            "local": True
        })
    
    providers.extend(local_providers)
    
    # Return up to 6 providers
    return providers[:6]

async def generate_implementation_insights(business_context: Dict, roadmap_content: str) -> str:
    """Generate research-backed implementation insights using RAG"""
    
    business_name = business_context.get('business_name', 'Your Business')
    industry = business_context.get('industry', 'general business')
    location = business_context.get('location', 'United States')
    business_type = business_context.get('business_type', 'startup')
    
    # Create comprehensive insights prompt
    insights_prompt = f"""
    Generate comprehensive, research-backed implementation insights for "{business_name}" - a {business_type} in the {industry} industry located in {location}.
    
    Business Context:
    - Business Name: {business_name}
    - Industry: {industry}
    - Location: {location}
    - Business Type: {business_type}
    
    Roadmap Content: {roadmap_content[:1000]}...
    
    Provide insights that include:
    1. Industry-specific implementation considerations
    2. Location-based regulatory and business requirements
    3. Business type specific challenges and opportunities
    4. Timeline and resource allocation recommendations
    5. Risk mitigation strategies
    6. Success metrics and milestones
    
    Make these insights actionable, specific, and tailored to their business context. 
    Focus on practical implementation guidance that will help them succeed.
    
    Format as clear, actionable insights with specific recommendations.
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": ANGEL_SYSTEM_PROMPT},
                {"role": "user", "content": insights_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating implementation insights: {e}")
        return f"Based on your {business_type} in the {industry} industry, implementation will require careful attention to {industry}-specific requirements and {location} regulations. Focus on building strong operational foundations and establishing clear processes for growth."

async def prepare_implementation_transition(session_data: Dict, roadmap_content: str) -> Dict:
    """Prepare comprehensive implementation transition data"""
    
    business_context = {
        "business_name": session_data.get('business_name', 'Your Business'),
        "industry": session_data.get('industry', 'general business'),
        "location": session_data.get('location', 'United States'),
        "business_type": session_data.get('business_type', 'startup')
    }
    
    try:
        # Get motivational quote
        motivational_quote = await get_motivational_quote(business_context)
        
        # Get service provider preview
        service_providers = await get_service_provider_preview(business_context)
        
        # Generate implementation insights
        implementation_insights = await generate_implementation_insights(business_context, roadmap_content)
        
        return {
            "success": True,
            "motivational_quote": motivational_quote,
            "service_providers": service_providers,
            "implementation_insights": implementation_insights,
            "business_context": business_context
        }
    except Exception as e:
        print(f"Error preparing implementation transition: {e}")
        return {
            "success": False,
            "error": str(e),
            "motivational_quote": MOTIVATIONAL_QUOTES[0],
            "service_providers": SERVICE_PROVIDER_CATEGORIES['legal'][:2],
            "implementation_insights": "Implementation insights generation in progress...",
            "business_context": business_context
        }

