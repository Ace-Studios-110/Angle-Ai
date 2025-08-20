from openai import AsyncOpenAI
import os
import json
import re
from utils.constant import ANGEL_SYSTEM_PROMPT

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TAG_PROMPT = "Reminder: Before asking the next question, include a machine-readable tag in this format:\n[[Q:<PHASE>.<NN>]] — e.g. [[Q:BUSINESS_PLAN.03]] What is your pricing model?"

WEB_SEARCH_PROMPT = """You have access to web search capabilities. Use web search when:
- Conducting competitive analysis
- Researching market trends and conditions
- Validating business ideas or market opportunities  
- Finding current vendor recommendations and pricing
- Checking regulatory/licensing requirements
- Verifying domain name availability suggestions

Always disclose to the user when you're conducting research: "Let me research this for you..." or "I'm conducting some background research..."

To use web search, include in your response: WEBSEARCH_QUERY: [your search query]"""

async def conduct_web_search(query):
    """Conduct web search using OpenAI's web search tool"""
    try:
        # Use OpenAI's web search tool (when available)
        response = await client.chat.completions.create(
            model="gpt-5",
            messages=[{
                "role": "user", 
                "content": f"Please search the web for: {query}"
            }],
            tools=[{"type": "web_search"}] if hasattr(client, 'tools') else None,
            temperature=0.3
        )
        
        # Extract search results from response
        search_results = response.choices[0].message.content
        return search_results
    
    except Exception as e:
        print(f"Web search error: {e}")
        return "I apologize, but I'm unable to conduct web research at this moment. I'll provide guidance based on my existing knowledge."

async def get_angel_reply(user_msg, history, session_data=None):
    # Always default to "hi" if input is empty
    if not user_msg.get("content") or user_msg["content"].strip() == "":
        user_msg["content"] = "hi"

    user_content = user_msg["content"].strip()
    
    # Check if web search is needed based on session phase and content
    needs_web_search = False
    web_search_query = None
    
    if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        # Look for competitive analysis, market research, or vendor recommendation needs
        business_keywords = ["competitors", "market", "industry", "trends", "pricing", "vendors", "domain", "legal requirements"]
        if any(keyword in user_content.lower() for keyword in business_keywords):
            needs_web_search = True
            
            # Extract or generate search query
            if "competitors" in user_content.lower():
                web_search_query = f"competitors in {session_data.get('industry', 'business')} industry"
            elif "market" in user_content.lower() or "trends" in user_content.lower():
                web_search_query = f"market trends {session_data.get('industry', 'business')} {session_data.get('location', '')}"
            elif "domain" in user_content.lower():
                web_search_query = "domain registration availability check websites"
    
    # Conduct web search if needed
    search_results = ""
    if needs_web_search and web_search_query:
        search_results = await conduct_web_search(web_search_query)

    # Build messages for OpenAI
    msgs = [
        {"role": "system", "content": ANGEL_SYSTEM_PROMPT},
        {"role": "system", "content": TAG_PROMPT},
        {"role": "system", "content": WEB_SEARCH_PROMPT}
    ]
    
    # Add search results if available
    if search_results:
        msgs.append({
            "role": "system", 
            "content": f"Web search results for your reference:\n{search_results}\n\nIntegrate relevant findings naturally into your response."
        })
    
    # Add conversation history and current message
    msgs.extend(history)
    msgs.append({"role": "user", "content": user_content})

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=msgs,
        temperature=0.7
    )

    reply_content = response.choices[0].message.content
    
    # Handle command processing
    if user_content.lower() == "draft":
        reply_content = handle_draft_command(reply_content, history)
    elif user_content.lower().startswith("scrapping:"):
        notes = user_content[10:].strip()
        reply_content = handle_scrapping_command(reply_content, notes, history)
    elif user_content.lower() == "support":
        reply_content = handle_support_command(reply_content, history)

    return reply_content

def handle_draft_command(reply, history):
    """Handle the Draft command"""
    # Extract context from conversation history
    context_summary = extract_conversation_context(history)
    
    draft_response = f"Here's a draft based on what you've shared:\n\n{reply}\n\n"
    draft_response += "Would you like to:\n• **Accept** this response and move forward\n• **Modify** - provide feedback to refine this answer"
    
    return draft_response

def handle_scrapping_command(reply, notes, history):
    """Handle the Scrapping command"""
    refined_response = f"Here's a refined version of your thoughts:\n\n{reply}\n\n"
    refined_response += "Would you like to:\n• **Accept** this response and move forward\n• **Modify** - provide feedback to refine this answer"
    
    return refined_response

def handle_support_command(reply, history):
    """Handle the Support command"""
    support_response = f"Let's work through this together with some deeper context:\n\n{reply}\n\n"
    support_response += "Here are some strategic questions to help you develop a stronger response:\n"
    
    # The AI should have generated strategic questions in the reply
    return support_response

def extract_conversation_context(history):
    """Extract relevant context from conversation history"""
    recent_messages = history[-6:] if len(history) > 6 else history
    context = []
    
    for msg in recent_messages:
        if msg["role"] == "user" and len(msg["content"]) > 10:
            context.append(msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"])
    
    return " | ".join(context)

async def generate_business_plan_artifact(session_data, conversation_history):
    """Generate comprehensive business plan artifact"""
    
    # Conduct additional research for business plan
    industry = session_data.get('industry', 'general business')
    location = session_data.get('location', 'United States')
    
    market_research = await conduct_web_search(f"market analysis {industry} {location} 2024")
    competitor_research = await conduct_web_search(f"top competitors {industry} business model analysis")
    
    business_plan_prompt = f"""
    Generate a comprehensive, detailed business plan based on the following conversation history and research:
    
    Session Data: {json.dumps(session_data, indent=2)}
    
    Recent Research:
    Market Analysis: {market_research}
    Competitor Analysis: {competitor_research}
    
    Conversation History: {json.dumps(conversation_history[-20:], indent=2)}
    
    Create a professional business plan that is in-depth, holistic, and highly detailed. This should blend the user's direct answers with research-driven insights to fill in gaps and provide comprehensive coverage of:
    
    1. Executive Summary
    2. Company Description  
    3. Market Analysis (with research-backed insights)
    4. Organization & Management
    5. Product/Service Offering
    6. Marketing & Sales Strategy
    7. Financial Projections
    8. Funding Requirements
    9. Risk Analysis
    10. Implementation Timeline
    
    Make this a trust-building milestone that demonstrates deep understanding of both the customer and their business opportunity.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": business_plan_prompt}],
        temperature=0.6
    )
    
    return response.choices[0].message.content

async def generate_roadmap_artifact(session_data, business_plan_data):
    """Generate comprehensive roadmap based on business plan"""
    
    # Research current tools and vendors
    industry = session_data.get('industry', 'general business')
    business_type = session_data.get('business_type', 'startup')
    
    vendor_research = await conduct_web_search(f"best business tools vendors {industry} {business_type} 2024")
    legal_research = await conduct_web_search(f"business formation requirements {session_data.get('location', 'United States')}")
    
    roadmap_prompt = f"""
    Create a detailed, chronological roadmap for launching this business:
    
    Business Context: {json.dumps(session_data, indent=2)}
    Business Plan Summary: {business_plan_data}
    
    Current Vendor Research: {vendor_research}
    Legal Requirements Research: {legal_research}
    
    Include:
    - Specific timelines and deadlines
    - Clear task ownership (Angel vs User)
    - 3 recommended vendors/platforms per category with current pricing
    - Industry-specific milestones
    - Pre-launch, launch, and post-launch phases
    - Critical path dependencies
    
    Make this actionable and comprehensive for immediate implementation.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": roadmap_prompt}],
        temperature=0.6
    )
    
    return response.choices[0].message.content