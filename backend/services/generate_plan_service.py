from openai import AsyncOpenAI
import os
import json
from datetime import datetime
from services.angel_service import generate_business_plan_artifact, conduct_web_search

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_full_business_plan(history):
    """Generate comprehensive business plan with deep research"""


    # Extract session data from conversation history
    session_data = {}
    conversation_history = []
    
    for msg in history:
        if isinstance(msg, dict):
            conversation_history.append(msg)
            content = msg.get('content', '').lower()
            
            # Extract industry information
            if any(keyword in content for keyword in ['industry', 'business type', 'sector', 'field']):
                # Try to extract industry from content
                if 'technology' in content:
                    session_data['industry'] = 'technology'
                elif 'food' in content or 'restaurant' in content:
                    session_data['industry'] = 'food'
                elif 'retail' in content:
                    session_data['industry'] = 'retail'
                elif 'consulting' in content:
                    session_data['industry'] = 'consulting'
                elif 'healthcare' in content:
                    session_data['industry'] = 'healthcare'
                elif 'education' in content:
                    session_data['industry'] = 'education'
                elif 'manufacturing' in content:
                    session_data['industry'] = 'manufacturing'
                elif 'real estate' in content:
                    session_data['industry'] = 'real estate'
                elif 'hospitality' in content:
                    session_data['industry'] = 'hospitality'
                else:
                    session_data['industry'] = 'general business'
            
            # Extract location information
            if any(keyword in content for keyword in ['location', 'city', 'country', 'state', 'region']):
                if 'united states' in content or 'usa' in content or 'us' in content:
                    session_data['location'] = 'United States'
                elif 'canada' in content:
                    session_data['location'] = 'Canada'
                elif 'united kingdom' in content or 'uk' in content:
                    session_data['location'] = 'United Kingdom'
                elif 'australia' in content:
                    session_data['location'] = 'Australia'
                else:
                    session_data['location'] = 'United States'  # Default
    
    # Set defaults if not found
    if 'industry' not in session_data:
        session_data['industry'] = 'general business'
    if 'location' not in session_data:
        session_data['location'] = 'United States'
    
    # Use the deep research business plan generation
    business_plan_content = await generate_business_plan_artifact(session_data, conversation_history)
    
    return {
        "plan": business_plan_content,
        "generated_at": datetime.now().isoformat(),
        "research_conducted": True,
        "industry": session_data['industry'],
        "location": session_data['location']
    }

async def generate_full_roadmap_plan(history):
    """Generate comprehensive roadmap with deep research"""
    
    # Extract session data from conversation history
    session_data = {}
    conversation_history = []
    
    for msg in history:
        if isinstance(msg, dict):
            conversation_history.append(msg)
            content = msg.get('content', '').lower()
            
            # Extract industry information
            if any(keyword in content for keyword in ['industry', 'business type', 'sector', 'field']):
                if 'technology' in content:
                    session_data['industry'] = 'technology'
                elif 'food' in content or 'restaurant' in content:
                    session_data['industry'] = 'food'
                elif 'retail' in content:
                    session_data['industry'] = 'retail'
                elif 'consulting' in content:
                    session_data['industry'] = 'consulting'
                elif 'healthcare' in content:
                    session_data['industry'] = 'healthcare'
                elif 'education' in content:
                    session_data['industry'] = 'education'
                elif 'manufacturing' in content:
                    session_data['industry'] = 'manufacturing'
                elif 'real estate' in content:
                    session_data['industry'] = 'real estate'
                elif 'hospitality' in content:
                    session_data['industry'] = 'hospitality'
                else:
                    session_data['industry'] = 'general business'
            
            # Extract location information
            if any(keyword in content for keyword in ['location', 'city', 'country', 'state', 'region']):
                if 'united states' in content or 'usa' in content or 'us' in content:
                    session_data['location'] = 'United States'
                elif 'canada' in content:
                    session_data['location'] = 'Canada'
                elif 'united kingdom' in content or 'uk' in content:
                    session_data['location'] = 'United Kingdom'
                elif 'australia' in content:
                    session_data['location'] = 'Australia'
                else:
                    session_data['location'] = 'United States'  # Default
    
    # Set defaults if not found
    if 'industry' not in session_data:
        session_data['industry'] = 'general business'
    if 'location' not in session_data:
        session_data['location'] = 'United States'
    
    # Conduct comprehensive research for roadmap
    industry = session_data.get('industry', 'general business')
    location = session_data.get('location', 'United States')
    
    current_year = datetime.now().year
    previous_year = current_year - 1
    
    print(f"🔍 Conducting deep research for {industry} roadmap in {location}")
    
    # Multiple research queries for comprehensive roadmap analysis
    startup_timeline_research = await conduct_web_search(f"startup launch timeline {industry} {location} {previous_year}")
    regulatory_requirements = await conduct_web_search(f"{industry} regulatory requirements startup {location} {previous_year}")
    funding_timeline = await conduct_web_search(f"{industry} funding timeline seed stage {previous_year}")
    market_entry_strategy = await conduct_web_search(f"{industry} market entry strategy startup {location} {previous_year}")
    
    ROADMAP_TEMPLATE = """
### 1. Executive Summary
Brief overview of the roadmap and expected outcomes.

### 2. Pre-Launch Phase (Months 1-3)
**Foundation Building**
- **Timeline**: Month 1-3
- **Action**: Complete business registration, legal setup, and initial team building
- **Angel Assistance**: I can help you navigate legal requirements, create job descriptions, and identify key hires
- **Recommended Tools/Vendors**: [Research-based recommendations]

### 3. Development Phase (Months 4-6)
**Product/Service Development**
- **Timeline**: Month 4-6
- **Action**: Build MVP, establish operations, and create initial marketing materials
- **Angel Assistance**: I can help you refine your MVP, create marketing strategies, and establish operational processes
- **Recommended Tools/Vendors**: [Research-based recommendations]

### 4. Launch Phase (Months 7-9)
**Market Entry**
- **Timeline**: Month 7-9
- **Action**: Soft launch, gather feedback, and refine offerings
- **Angel Assistance**: I can help you plan launch strategies, analyze feedback, and optimize your approach
- **Recommended Tools/Vendors**: [Research-based recommendations]

### 5. Growth Phase (Months 10-12)
**Scale and Optimize**
- **Timeline**: Month 10-12
- **Action**: Scale operations, expand market reach, and optimize processes
- **Angel Assistance**: I can help you identify scaling opportunities, optimize operations, and plan expansion strategies
- **Recommended Tools/Vendors**: [Research-based recommendations]

### 6. Industry-Specific Considerations
- **Regulatory Requirements**: [Research-based insights]
- **Market Timing**: [Research-based insights]
- **Competitive Landscape**: [Research-based insights]

### 7. Success Metrics & Milestones
- **Key Performance Indicators**: [Industry-specific metrics]
- **Monthly Checkpoints**: [Detailed milestone tracking]

### 8. Angel's Ongoing Support
Throughout this roadmap, I'll be available to:
- Help you navigate each phase with detailed guidance
- Provide industry-specific insights and recommendations
- Assist with problem-solving and decision-making
- Connect you with relevant resources and tools

**Formatting Requirements:**
- Bold all step titles and key terms
- Use bullet lists for clarity
- Use a professional but friendly tone
- Include tables for tools if possible
- Remove "Owner" field as Angel will assist throughout
"""

    messages = [
        {
            "role": "system",
            "content": (
                "You are Angel, an AI startup coach specialized in crafting execution-ready business roadmaps with deep research. "
                "Based on the user's KYC and Business Plan information, generate a comprehensive, research-backed roadmap "
                "that guides the founder step-by-step to launch and grow their venture. "
                "Use the provided research data to make informed recommendations about timelines, tools, and strategies. "
                "Always emphasize how Angel can assist throughout the process. "
                "Use clear, friendly tone, markdown formatting, and React-friendly output."
            )
        },
        {
            "role": "user",
            "content": (
                f"Generate a comprehensive startup roadmap based on the user's information and extensive research:\n\n"
                f"Session Data: {json.dumps(session_data, indent=2)}\n\n"
                f"Deep Research Conducted:\n"
                f"Startup Timeline Research: {startup_timeline_research}\n"
                f"Regulatory Requirements: {regulatory_requirements}\n"
                f"Funding Timeline: {funding_timeline}\n"
                f"Market Entry Strategy: {market_entry_strategy}\n\n"
                f"Conversation History: {json.dumps(conversation_history[-20:], indent=2)}\n\n"
                f"Follow this template structure:\n{ROADMAP_TEMPLATE}\n\n"
                f"**Important Notes:**\n"
                f"- This roadmap incorporates deep research and industry analysis\n"
                f"- Angel will assist throughout the entire process\n"
                f"- Remove 'Owner' field as Angel provides ongoing support\n"
                f"- Include specific, actionable steps with realistic timelines\n"
                f"- Provide industry-specific insights and recommendations"
            )
        }
    ]

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )

    return {
        "plan": response.choices[0].message.content,
        "generated_at": datetime.now().isoformat(),
        "research_conducted": True,
        "industry": session_data['industry'],
        "location": session_data['location']
    }
