from openai import AsyncOpenAI
import os
import json
import re
from datetime import datetime
from utils.constant import ANGEL_SYSTEM_PROMPT

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TAG_PROMPT = """CRITICAL: You MUST include a machine-readable tag in EVERY response that contains a question. Use this exact format:
[[Q:<PHASE>.<NN>]] 

Examples:
- [[Q:KYC.01]] What's your name?
- [[Q:KYC.02]] What is your preferred communication style?
- [[Q:BUSINESS_PLAN.01]] What is your business idea?

The tag must be at the beginning of your question, before any other text. This is essential for progress tracking.

FAILURE TO INCLUDE TAGS WILL BREAK THE SYSTEM. ALWAYS include the tag before asking any question.

FORMATTING REQUIREMENT: Always use structured format for questions - NEVER paragraph format!"""

WEB_SEARCH_PROMPT = """You have access to web search capabilities. Use web search when:
- Conducting competitive analysis
- Researching market trends and conditions
- Validating business ideas or market opportunities  
- Finding current vendor recommendations and pricing
- Checking regulatory/licensing requirements
- Verifying domain name availability suggestions

WEB SEARCH GUIDELINES:
• When web search results are provided, you MUST include them in your response immediately
• Use previous calendar year for search queries (e.g., "2024" instead of "2023")
• Provide comprehensive answers based on the research findings
• Do not ask the user to wait or send another message - deliver results immediately
• Include specific details from the research in your response
• Do not just say "I'm conducting research" - provide the actual research results

To use web search, include in your response: WEBSEARCH_QUERY: [your search query]"""

async def conduct_web_search(query):
    """Conduct web search using OpenAI's web search tool with progress indication"""
    try:
        print(f"🔍 Conducting web search: {query}")
        
        # Use a faster, more efficient approach
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Use faster model for web search
            messages=[{
                "role": "user", 
                "content": f"Search for current information about: {query}. Provide a concise summary of key findings."
            }],
            temperature=0.1,  # Lower temperature for more focused results
            max_tokens=500  # Limit response length for faster processing
        )
        
        # Extract search results from response
        search_results = response.choices[0].message.content
        print(f"✅ Web search completed for: {query}")
        return search_results
    
    except Exception as e:
        print(f"❌ Web search error: {e}")
        return "I apologize, but I'm unable to conduct web research at this moment. I'll provide guidance based on my existing knowledge."

def trim_conversation_history(history, max_messages=10):
    """Trim conversation history to prevent context from growing too large"""
    if len(history) <= max_messages:
        return history
    
    # Keep the most recent messages
    return history[-max_messages:]

def format_response_structure(reply):
    """Format AI responses to use proper structured format instead of paragraph form"""
    
    formatted_reply = reply
    
    # Specific formatting for work situation question
    if "work situation" in formatted_reply.lower() and "?" in formatted_reply:
        # Pattern: "What's your current work situation? Full-time employed Part-time Student Unemployed Self-employed/freelancer Other"
        work_pattern = r'([^?]+\?)\s+(Full-time employed\s+Part-time\s+Student\s+Unemployed\s+Self-employed/freelancer\s+Other)'
        formatted_reply = re.sub(work_pattern, 
            r'\1\n\n• Full-time employed\n• Part-time\n• Student\n• Unemployed\n• Self-employed/freelancer\n• Other', 
            formatted_reply)
    
    # Specific formatting for business before question
    if "business before" in formatted_reply.lower() and "?" in formatted_reply:
        # Pattern: "Have you started a business before? Yes / No"
        business_pattern = r'([^?]+\?)\s+(Yes\s*/\s*No)'
        formatted_reply = re.sub(business_pattern, r'\1\n\n\2', formatted_reply)
    
    # General pattern for multiple choice questions
    # Pattern: "Question? Option1 Option2 Option3 Option4"
    multi_choice_pattern = r'([^?]+\?)\s+([A-Za-z\s]+(?:employed|time|Student|Unemployed|freelancer|Other|Yes|No)[^?]*)'
    formatted_reply = re.sub(multi_choice_pattern, 
        lambda m: f"{m.group(1)}\n\n• {m.group(2).replace(' ', ' • ')}", 
        formatted_reply)
    
    # Clean up any double bullet points
    formatted_reply = re.sub(r'•\s*•\s*', '• ', formatted_reply)
    
    # Ensure proper spacing
    formatted_reply = re.sub(r'\n{3,}', '\n\n', formatted_reply)
    
    return formatted_reply

def ensure_question_separation(reply, session_data=None):
    """Ensure questions are properly separated and not combined"""
    
    # Check if this is a business plan question that might be combined
    if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        # Look for patterns where multiple questions are combined
        combined_patterns = [
            # Pattern: "Question1? Question2?"
            (r'([^?]+\?)\s+([A-Z][^?]+\?)', r'\1\n\n\2'),
            # Pattern: "Question1. Question2?"
            (r'([^?]+\.)\s+([A-Z][^?]+\?)', r'\1\n\n\2'),
        ]
        
        for pattern, replacement in combined_patterns:
            reply = re.sub(pattern, replacement, reply)
    
    return reply

def validate_business_plan_sequence(reply, session_data=None):
    """Ensure business plan questions follow proper sequence"""
    
    if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        # Extract current question number from tag
        tag_match = re.search(r'\[\[Q:BUSINESS_PLAN\.(\d+)\]\]', reply)
        if tag_match:
            current_q_num = int(tag_match.group(1))
            asked_q = session_data.get("asked_q", "BUSINESS_PLAN.01")
            
            # Check if we're jumping ahead
            if "BUSINESS_PLAN." in asked_q:
                last_q_num = int(asked_q.split(".")[1])
                if current_q_num > last_q_num + 1:
                    print(f"⚠️ WARNING: Jumping from question {last_q_num} to {current_q_num}")
                    # Force back to next sequential question
                    next_q = f"BUSINESS_PLAN.{last_q_num + 1:02d}"
                    reply = re.sub(r'\[\[Q:BUSINESS_PLAN\.\d+\]\]', f'[[Q:{next_q}]]', reply)
                    print(f"🔧 Corrected to: {next_q}")
    
    return reply

def fix_verification_flow(reply, session_data=None):
    """Fix verification flow to separate verification from next question"""
    
    if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        # Look for patterns where verification is combined with next question
        verification_patterns = [
            # Pattern: "Here's what I've captured... Does this look accurate? [Next question]"
            (r'(Here\'s what I\'ve captured so far:.*?Does this look accurate to you\?)\s+([A-Z][^?]+\?)', 
             r'\1\n\nPlease respond with "Accept" or "Modify" to continue.'),
            
            # Pattern: "Feel free to refine... What specific products..."
            (r'(Feel free to refine or expand on this as we continue\.)\s+([A-Z][^?]+\?)', 
             r'Does this information look accurate to you? If not, please let me know where you\'d like to modify and we\'ll work through this some more.\n\nPlease respond with "Accept" or "Modify" to continue.'),
        ]
        
        for pattern, replacement in verification_patterns:
            reply = re.sub(pattern, replacement, reply, flags=re.DOTALL)
        
        # Check if this is a verification message that should trigger Accept/Modify buttons
        verification_keywords = [
            "does this look accurate",
            "does this look correct", 
            "is this accurate",
            "is this correct",
            "please let me know where you'd like to modify"
        ]
        
        if any(keyword in reply.lower() for keyword in verification_keywords):
            # Ensure it ends with proper instruction
            if "Please respond with \"Accept\" or \"Modify\"" not in reply:
                reply += "\n\nPlease respond with \"Accept\" or \"Modify\" to continue."
    
    return reply

def prevent_ai_molding(reply, session_data=None):
    """Prevent AI from molding user answers into mission, vision, USP without verification"""
    
    if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        # Look for patterns where AI molds answers without verification
        molding_patterns = [
            # Pattern: AI creates mission, vision, USP from user input without asking
            (r'(Based on your input, here\'s what I\'ve created for you:.*?Mission:.*?Vision:.*?Unique Selling Proposition:.*?)([A-Z][^?]+\?)', 
             r'Here\'s what I\'ve captured so far: [summary]. Does this look accurate to you? If not, please let me know where you\'d like to modify and we\'ll work through this some more.\n\nPlease respond with "Accept" or "Modify" to continue.'),
            
            # Pattern: AI summarizes and immediately asks next question
            (r'(Great! Based on your answers, here\'s what I understand:.*?)([A-Z][^?]+\?)', 
             r'Here\'s what I\'ve captured so far: [summary]. Does this look accurate to you? If not, please let me know where you\'d like to modify and we\'ll work through this some more.\n\nPlease respond with "Accept" or "Modify" to continue.'),
        ]
        
        for pattern, replacement in molding_patterns:
            reply = re.sub(pattern, replacement, reply, flags=re.DOTALL)
        
        # Check if AI is molding without verification
        molding_keywords = [
            "based on your input, here's what i've created",
            "here's what i understand about your business",
            "let me create a mission statement for you",
            "based on your answers, here's your mission"
        ]
        
        if any(keyword in reply.lower() for keyword in molding_keywords):
            # Replace with proper verification request
            reply = "Here's what I've captured so far: [summary]. Does this look accurate to you? If not, please let me know where you'd like to modify and we'll work through this some more.\n\nPlease respond with \"Accept\" or \"Modify\" to continue."
    
    return reply

def suggest_draft_if_relevant(reply, session_data, user_input, history):
    """Suggest using Draft if user has already provided relevant information"""
    
    if not history or not user_input:
        return reply
    
    # Keywords that indicate the user might have already provided relevant information
    relevant_keywords = {
        'target audience': ['audience', 'customers', 'demographic', 'market', 'millennials', 'gen z', 'generation'],
        'business name': ['name', 'brand', 'company', 'business'],
        'products/services': ['product', 'service', 'offer', 'sell', 'provide'],
        'mission/vision': ['mission', 'vision', 'purpose', 'goal', 'objective'],
        'location': ['location', 'city', 'country', 'area', 'region'],
        'industry': ['industry', 'sector', 'field', 'business type'],
        'resources': ['resources', 'tools', 'equipment', 'staff', 'team', 'budget']
    }
    
    # Check if current question matches any of these categories
    current_question = reply.lower()
    relevant_category = None
    
    for category, keywords in relevant_keywords.items():
        if any(keyword in current_question for keyword in keywords):
            relevant_category = category
            break
    
    if relevant_category:
        # Check if user has provided information in this category before
        user_has_relevant_info = False
        
        # Check conversation history for relevant information
        for msg in history:
            if msg.get('role') == 'user' and len(msg.get('content', '')) > 10:
                user_content = msg['content'].lower()
                if any(keyword in user_content for keyword in relevant_keywords[relevant_category]):
                    user_has_relevant_info = True
                    break
        
        if user_has_relevant_info:
            # Add suggestion to use Draft
            draft_suggestion = f"\n\n💡 **Quick Tip**: Based on some info you've previously entered, you can also select **\"Draft\"** and I'll use that information to create a draft answer for you to review and save you some time."
            reply += draft_suggestion
    
    return reply

def check_for_section_summary(current_tag, session_data, history):
    """Check if we need to provide a section summary based on the current question tag"""
    
    if not current_tag or not current_tag.startswith("BUSINESS_PLAN."):
        return None
    
    try:
        question_num = int(current_tag.split(".")[1])
    except (ValueError, IndexError):
        return None
    
    # Define section boundaries and their summary requirements
    section_boundaries = {
        4: "SECTION 1 SUMMARY REQUIRED: After BUSINESS_PLAN.04, provide:",
        8: "SECTION 2 SUMMARY REQUIRED: After BUSINESS_PLAN.08, provide:",
        12: "SECTION 3 SUMMARY REQUIRED: After BUSINESS_PLAN.12, provide:",
        17: "SECTION 4 SUMMARY REQUIRED: After BUSINESS_PLAN.17, provide:",
        25: "SECTION 5 SUMMARY REQUIRED: After BUSINESS_PLAN.25, provide:",
        31: "SECTION 6 SUMMARY REQUIRED: After BUSINESS_PLAN.31, provide:",
        38: "SECTION 7 SUMMARY REQUIRED: After BUSINESS_PLAN.38, provide:",
        42: "SECTION 8 SUMMARY REQUIRED: After BUSINESS_PLAN.42, provide:",
        46: "SECTION 9 SUMMARY REQUIRED: After BUSINESS_PLAN.46, provide:"
    }
    
    # Check if we're at a section boundary
    if question_num in section_boundaries:
        return {
            "trigger_question": question_num,
            "summary_type": section_boundaries[question_num],
            "section_name": get_section_name(question_num)
        }
    
    return None

def get_section_name(question_num):
    """Get the section name based on question number"""
    section_names = {
        4: "Business Foundation",
        8: "Product/Service Details", 
        12: "Market Research",
        17: "Location & Operations",
        25: "Financial Planning",
        31: "Marketing & Sales",
        38: "Legal & Compliance",
        42: "Growth & Scaling",
        46: "Risk Management"
    }
    return section_names.get(question_num, "Unknown Section")

def add_critiquing_insights(reply, session_data=None, user_input=None):
    """Add critiquing insights and coaching based on user's business field (50/50 approach)"""
    
    if not user_input or not session_data:
        return reply
    
    # Extract business-related keywords from user input
    business_keywords = {
        "social media": ["social media", "instagram", "tiktok", "youtube", "influencer", "content creator", "wine critic", "short-form videos"],
        "food": ["restaurant", "food", "cooking", "chef", "culinary", "dining", "wine", "beverage"],
        "technology": ["app", "software", "tech", "digital", "online", "platform", "website", "mobile"],
        "retail": ["store", "shop", "retail", "product", "selling", "ecommerce", "marketplace"],
        "services": ["service", "consulting", "coaching", "training", "professional", "review", "critique"],
        "health": ["health", "fitness", "wellness", "medical", "therapy", "nutrition"],
        "education": ["education", "teaching", "learning", "course", "training", "tutorial"],
        "entertainment": ["entertainment", "music", "art", "creative", "media", "video", "content"]
    }
    
    # Identify the business field
    user_input_lower = user_input.lower()
    identified_field = None
    
    for field, keywords in business_keywords.items():
        if any(keyword in user_input_lower for keyword in keywords):
            identified_field = field
            break
    
    # Add critiquing insights based on the field (50/50 approach)
    if identified_field:
        critiquing_insights = {
            "social media": "Social media influencing is a very popular field with significant opportunities. Some of the most successful influencers cross-post to different platforms like YouTube, Threads, and LinkedIn to ensure reach and expand their audiences. Podcasts are also an interesting medium that has gained significant popularity in recent years. Consider building a consistent brand voice across all platforms.",
            "food": "The food and beverage industry is highly competitive but rewarding for those who find their niche. Successful food businesses often focus on unique flavors, local sourcing, and creating memorable experiences. Wine criticism, in particular, has seen growth with the rise of social media sommeliers. Consider the importance of food safety certifications and local health department requirements.",
            "technology": "The tech industry moves quickly, so staying updated with trends is crucial for success. Consider the importance of user experience design, scalability, and data security. Many successful tech startups begin with a minimum viable product (MVP) approach to test market demand before full development.",
            "retail": "Retail success often depends on understanding your target market and creating a strong brand identity. Consider both online and offline presence, inventory management, and customer service excellence. The key is finding the right balance between quality and accessibility.",
            "services": "Service-based businesses rely heavily on reputation and word-of-mouth marketing. Consider the importance of building strong client relationships, maintaining consistent quality, and having clear service agreements. Reviews and testimonials are particularly valuable in this space.",
            "health": "Health-related businesses require careful attention to regulations and certifications. Consider the importance of building trust with clients, maintaining confidentiality, and staying current with industry standards. Credibility and expertise are essential in this field.",
            "education": "Education businesses thrive on creating engaging learning experiences. Consider the importance of curriculum design, student engagement, and measuring learning outcomes. The best educational content combines practical knowledge with interactive elements.",
            "entertainment": "Entertainment businesses often succeed through unique content and strong audience engagement. Consider the importance of building a loyal following and creating content that resonates with your target audience. Consistency and authenticity are key to long-term success."
        }
        
        insight = critiquing_insights.get(identified_field)
        if insight:
            # Insert the insight after the acknowledgment but before the question
            lines = reply.split('\n')
            for i, line in enumerate(lines):
                if '?' in line and len(line.strip()) > 10:
                    # Insert insight before the question
                    lines.insert(i, f"\n{insight}\n")
                    break
            
            reply = '\n'.join(lines)
    
    return reply

def identify_support_areas(session_data, history):
    """Proactively identify areas where the entrepreneur needs the most support based on KYC and business plan answers"""
    
    if not session_data or not history:
        return None
    
    # Analyze conversation history for gaps and areas needing support
    support_areas = []
    
    # Check for common areas that need support
    conversation_text = " ".join([msg.get('content', '') for msg in history if msg.get('role') == 'user'])
    conversation_lower = conversation_text.lower()
    
    # Financial planning support
    if any(keyword in conversation_lower for keyword in ['budget', 'funding', 'money', 'cost', 'price', 'financial']):
        if not any(keyword in conversation_lower for keyword in ['detailed financial', 'financial projections', 'break even', 'revenue model']):
            support_areas.append("Financial Planning & Projections")
    
    # Market research support
    if any(keyword in conversation_lower for keyword in ['market', 'customers', 'competition', 'target']):
        if not any(keyword in conversation_lower for keyword in ['market research', 'competitive analysis', 'customer demographics', 'market size']):
            support_areas.append("Market Research & Competitive Analysis")
    
    # Operations support
    if any(keyword in conversation_lower for keyword in ['business', 'operations', 'process', 'staff']):
        if not any(keyword in conversation_lower for keyword in ['operational plan', 'staffing plan', 'processes', 'systems']):
            support_areas.append("Operations & Process Planning")
    
    # Legal/compliance support
    if any(keyword in conversation_lower for keyword in ['legal', 'license', 'permit', 'regulation', 'compliance']):
        if not any(keyword in conversation_lower for keyword in ['business structure', 'licenses required', 'legal requirements']):
            support_areas.append("Legal Structure & Compliance")
    
    # Marketing support
    if any(keyword in conversation_lower for keyword in ['marketing', 'sales', 'customers', 'brand']):
        if not any(keyword in conversation_lower for keyword in ['marketing strategy', 'sales process', 'brand positioning', 'customer acquisition']):
            support_areas.append("Marketing & Sales Strategy")
    
    # Technology support
    if any(keyword in conversation_lower for keyword in ['technology', 'software', 'website', 'digital', 'online']):
        if not any(keyword in conversation_lower for keyword in ['technology requirements', 'digital tools', 'software needs']):
            support_areas.append("Technology & Digital Tools")
    
    return support_areas

def add_proactive_support_guidance(reply, session_data, history):
    """Add proactive support guidance based on identified areas needing help"""
    
    support_areas = identify_support_areas(session_data, history)
    
    if support_areas:
        support_guidance = "\n\n**🎯 Areas Where You May Need Additional Support:**\n"
        support_guidance += "Based on your responses, I've identified these areas where you might benefit from deeper guidance:\n\n"
        
        for area in support_areas:
            support_guidance += f"• **{area}** - Consider using 'Support' for detailed guidance in this area\n"
        
        support_guidance += "\n💡 **Pro Tip:** Use 'Support' followed by any of these areas for comprehensive guidance and strategic questions to help you think through these topics more thoroughly."
        
        reply += support_guidance
    
    return reply

def ensure_proper_question_formatting(reply, session_data=None):
    """Ensure questions are properly formatted with line breaks and structure"""
    
    # Look for patterns where questions are not properly formatted
    formatting_patterns = [
        # Pattern: Question without proper line breaks
        (r'([^?]+\?)\s+([A-Z][^?]+)', r'\1\n\n\2'),
        # Pattern: Multiple choice options without proper formatting
        (r'([^?]+\?)\s+([A-Z][^?]+(?:employed|time|Student|Unemployed|freelancer|Other|Yes|No)[^?]*)', 
         r'\1\n\n• \2'),
    ]
    
    for pattern, replacement in formatting_patterns:
        reply = re.sub(pattern, replacement, reply)
    
    # Ensure proper spacing between sections
    reply = re.sub(r'\n{3,}', '\n\n', reply)
    
    return reply

def inject_missing_tag(reply, session_data=None):
    """Inject a tag if the AI forgot to include one"""
    # Check if reply already has a tag
    if "[[Q:" in reply:
        return reply
    
    # Try to determine the current phase and question number
    current_phase = "KYC"  # Default
    question_num = "01"    # Default
    
    if session_data:
        current_phase = session_data.get("current_phase", "KYC")
        asked_q = session_data.get("asked_q", "KYC.01")
        if "." in asked_q:
            phase, num = asked_q.split(".")
            current_phase = phase
            try:
                next_num = int(num) + 1
                question_num = f"{next_num:02d}"
            except:
                question_num = "01"
    
    # If this looks like a question (contains ?), inject a tag
    if "?" in reply and len(reply.strip()) > 10:
        tag = f"[[Q:{current_phase}.{question_num}]]"
        # Insert tag at the beginning of the first sentence that contains a question
        lines = reply.split('\n')
        for i, line in enumerate(lines):
            if '?' in line and len(line.strip()) > 10:
                # Clean up the line and add tag
                clean_line = line.strip()
                lines[i] = f"{tag} {clean_line}"
                break
        return '\n'.join(lines)
    
    return reply

async def get_angel_reply(user_msg, history, session_data=None):
    import time
    start_time = time.time()
    
    # Always default to "hi" if input is empty
    if not user_msg.get("content") or user_msg["content"].strip() == "":
        user_msg["content"] = "hi"

    user_content = user_msg["content"].strip()
    print(f"🚀 Starting Angel reply generation for: {user_content[:50]}...")
    
    # Handle Accept response for verification
    if user_content.lower() == "accept":
        return "Great! Let's move to the next question..."
    
    # Add instruction for proper question formatting
    FORMATTING_INSTRUCTION = """
CRITICAL FORMATTING RULES - FOLLOW EXACTLY:

1. ALWAYS start with a brief acknowledgment (1-2 sentences max)
2. Add a blank line for visual separation
3. Present the question in a clear, structured format:

For YES/NO questions:
"That's great, Ahmed!

Have you started a business before?
Yes / No"

For multiple choice questions:
"That's perfect, Ahmed!

What's your current work situation?
• Full-time employed
• Part-time
• Student
• Unemployed
• Self-employed/freelancer
• Other"

For rating questions:
"That's helpful, Ahmed!

How comfortable are you with business planning?
○ ○ ○ ○ ○
1  2  3  4  5"

For verification steps:
"That's excellent, Ahmed!

Here's what I've captured so far:
[Summary of information]

Does this look accurate to you? If not, please let me know where you'd like to modify and we'll work through this some more."

❌ NEVER DO THIS: "What's your current work situation? Full-time employed Part-time Student Unemployed Self-employed/freelancer Other"

✅ ALWAYS DO THIS: "What's your current work situation?
• Full-time employed
• Part-time
• Student
• Unemployed
• Self-employed/freelancer
• Other"

BUSINESS PLAN SPECIFIC RULES:
• Ask ONE question at a time in EXACT sequential order
• After every 3-4 questions, provide verification step
• Wait for user acknowledgment before proceeding
• Never combine questions or skip verification steps
• Each question must be on its own line with proper spacing
• Use verification format: "Here's what I've captured so far: [summary]. Does this look accurate to you?"
• NEVER mold user answers into mission, vision, USP without explicit verification
• Start with BUSINESS_PLAN.01 and proceed sequentially
• Do NOT jump to later questions or combine multiple questions

VERIFICATION FLOW REQUIREMENTS:
• When providing verification, ONLY show the verification message
• Do NOT combine verification with the next question
• Wait for user response (Accept/Modify) before proceeding
• After user accepts, show brief acknowledgment: "Great! Let's move to the next question..."
• Then ask the next sequential question

CRITIQUING SYSTEM (50/50 APPROACH):
• **50% Positive Acknowledgment**: Always start with supportive, encouraging response to their answer
• **50% Educational Coaching**: Identify opportunities to coach the user based on their information
• **Critiquing Guidelines**: 
  - Don't be critical, but critique their answer constructively
  - Offer insightful information that helps them better understand the business space they're entering
  - Provide high-value education that pertains to their answer and business field
  - Include specific examples, best practices, and actionable insights
  - Focus on opportunities and growth rather than problems
• Example: "Social media influencing is a very popular field. Some of the most successful influencers cross-post to different platforms like YouTube, Threads, etc. to ensure reach and expand their audiences. Podcasts are also an interesting medium that has gained significant popularity in recent years."

Do NOT include question numbers, progress percentages, or step counts in your response.
"""
    
    # Check if web search is needed based on session phase and content
    needs_web_search = False
    web_search_query = None
    
    if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        # Look for competitive analysis, market research, or vendor recommendation needs
        business_keywords = ["competitors", "market", "industry", "trends", "pricing", "vendors", "domain", "legal requirements"]
        if any(keyword in user_content.lower() for keyword in business_keywords):
            needs_web_search = True
            
            # Extract or generate search query with previous calendar year
            current_year = datetime.now().year
            previous_year = current_year - 1
            
            if "competitors" in user_content.lower():
                web_search_query = f"competitors in {session_data.get('industry', 'business')} industry {previous_year}"
            elif "market" in user_content.lower() or "trends" in user_content.lower():
                web_search_query = f"market trends {session_data.get('industry', 'business')} {session_data.get('location', '')} {previous_year}"
            elif "domain" in user_content.lower():
                web_search_query = "domain registration availability check websites"
            elif "wine" in user_content.lower() or "influencer" in user_content.lower():
                web_search_query = f"top wine influencers on social media {previous_year}"
    
    # Conduct web search if needed
    search_results = ""
    web_search_status = {"is_searching": False, "query": None}
    immediate_response = None
    
    if needs_web_search and web_search_query:
        # Set web search status for progress indicator
        web_search_status = {"is_searching": True, "query": web_search_query}
        
        # Provide immediate feedback to user
        immediate_response = f"I'm conducting some background research on '{web_search_query}' to provide you with the most current information. This will just take a moment..."
        
        # Conduct the search
        search_start = time.time()
        search_results = await conduct_web_search(web_search_query)
        search_time = time.time() - search_start
        print(f"🔍 Web search completed in {search_time:.2f} seconds")
        
        # Update status to completed
        web_search_status = {"is_searching": False, "query": web_search_query, "completed": True}
        
        # If search was successful, include results in the response
        if search_results and "unable to conduct web research" not in search_results:
            search_results = f"\n\nResearch Results:\n{search_results}"

    # Build messages for OpenAI - optimized for speed
    msgs = [
        {"role": "system", "content": ANGEL_SYSTEM_PROMPT},
        {"role": "system", "content": TAG_PROMPT},
        {"role": "system", "content": FORMATTING_INSTRUCTION}
    ]
    
    # Only add web search prompt if web search was conducted
    if search_results:
        msgs.append({"role": "system", "content": WEB_SEARCH_PROMPT})
    
    # Add search results and immediate response if available
    if search_results:
        msgs.append({
            "role": "system", 
            "content": f"Web search results for your reference:\n{search_results}\n\nIntegrate relevant findings naturally into your response."
        })
    
    # Add immediate response instruction if web search was conducted
    if immediate_response:
        msgs.append({
            "role": "system",
            "content": f"IMPORTANT: The user has requested research and search results have been provided above. You MUST include the research findings in your response. Do not just acknowledge the research - provide the actual results and answer their question based on the search findings. The user expects to get the research results immediately, not just a notification that research is being conducted."
        })
    
    # Add conversation history (trimmed for performance) and current message
    trimmed_history = trim_conversation_history(history, max_messages=10)
    msgs.extend(trimmed_history)
    msgs.append({"role": "user", "content": user_content})

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=msgs,
        temperature=0.7,
        max_tokens=1000,  # Limit response length for faster processing
        stream=False  # Ensure non-streaming for consistent response times
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
    elif user_content.lower() == "kickstart":
        reply_content = handle_kickstart_command(reply_content, history, session_data)
    elif user_content.lower() == "who do i contact?":
        reply_content = handle_contact_command(reply_content, history, session_data)
    
    # Inject missing tag if AI forgot to include one
    reply_content = inject_missing_tag(reply_content, session_data)
    
    # Format response structure to use proper list format instead of paragraph
    reply_content = format_response_structure(reply_content)
    
    # Ensure questions are properly separated
    reply_content = ensure_question_separation(reply_content, session_data)
    
    # Validate business plan question sequence
    reply_content = validate_business_plan_sequence(reply_content, session_data)
    
    # Fix verification flow to separate verification from next question
    reply_content = fix_verification_flow(reply_content, session_data)
    
    # Prevent AI from molding user answers without verification
    reply_content = prevent_ai_molding(reply_content, session_data)
    
    # Add critiquing insights based on user's business field
    reply_content = add_critiquing_insights(reply_content, session_data, user_content)
    
    # Suggest using Draft if user has already provided relevant information
    reply_content = suggest_draft_if_relevant(reply_content, session_data, user_content, history)
    
    # Add proactive support guidance based on identified areas needing help
    reply_content = add_proactive_support_guidance(reply_content, session_data, history)
    
    # Check if we need to provide a section summary
    current_tag = session_data.get("asked_q") if session_data else None
    section_summary_info = check_for_section_summary(current_tag, session_data, history)
    
    if section_summary_info:
        # Add section summary requirements to the system prompt
        summary_instruction = f"""
IMPORTANT: You have just completed {section_summary_info['section_name']} section. 
You MUST provide a comprehensive section summary that includes:

1. **Summary**: Recap the key information provided in this section
2. **Educational Insights**: Provide valuable insights about this business area
3. **Critical Considerations**: Highlight important watchouts and considerations for this business type
4. **Verification Request**: Ask user to verify the information before proceeding

Use this format:
"🎯 **{section_summary_info['section_name']} Section Complete**

**Summary of Your Information:**
[Recap key points from this section]

**Educational Insights:**
[Provide valuable business insights related to this section]

**Critical Considerations:**
[Highlight important watchouts and things to consider]

**Verification:**
Here's what I've captured so far: [summary]. Does this look accurate to you? If not, please let me know where you'd like to modify and we'll work through this some more."
"""
        # Add this instruction to the messages
        msgs.append({"role": "system", "content": summary_instruction})
        
        # Regenerate the response with section summary
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=msgs,
            temperature=0.7,
            max_tokens=1000,
            stream=False
        )
        reply_content = response.choices[0].message.content
    
    # Ensure proper question formatting with line breaks and structure
    reply_content = ensure_proper_question_formatting(reply_content, session_data)

    end_time = time.time()
    response_time = end_time - start_time
    print(f"⏱️ Angel reply generated in {response_time:.2f} seconds")
    
    return {
        "reply": reply_content,
        "web_search_status": web_search_status,
        "immediate_response": immediate_response
    }

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
    
    # Add comprehensive guidance instead of leaving cliffhangers
    support_response += "**Strategic Questions to Consider:**\n"
    support_response += "• What specific challenges are you trying to solve?\n"
    support_response += "• Who are your primary stakeholders and decision-makers?\n"
    support_response += "• What resources do you currently have available?\n"
    support_response += "• What are your biggest concerns or uncertainties?\n"
    support_response += "• How will you measure success?\n\n"
    
    support_response += "**Next Steps:**\n"
    support_response += "• Take time to think through these questions\n"
    support_response += "• Consider your unique situation and constraints\n"
    support_response += "• Feel free to ask for clarification on any specific aspect\n"
    support_response += "• You can also use 'Draft' to have me create a comprehensive response based on your previous answers\n\n"
    
    support_response += "**Ready to Move Forward?**\n"
    support_response += "Do you want me to use this information to answer this question? If you want to use portions of this information, or see additional info, just let me know and we'll work through it together."
    
    return support_response

def handle_kickstart_command(reply, history, session_data):
    """Handle the Kickstart command"""
    kickstart_response = f"Here are some kickstart resources to get you moving:\n\n{reply}\n\n"
    kickstart_response += "These templates and frameworks are customized for your business context. "
    kickstart_response += "Would you like me to:\n• **Customize** these further for your specific needs\n• **Provide** additional templates or checklists\n• **Move forward** with the current resources"
    
    return kickstart_response

def handle_contact_command(reply, history, session_data):
    """Handle the Who do I contact? command"""
    contact_response = f"Based on your business needs, here are some trusted professionals:\n\n{reply}\n\n"
    contact_response += "These recommendations are tailored to your industry, location, and business stage. "
    contact_response += "Would you like me to:\n• **Research** more specific providers in your area\n• **Provide** contact templates for reaching out\n• **Suggest** questions to ask when interviewing them"
    
    return contact_response

def extract_conversation_context(history):
    """Extract relevant context from conversation history"""
    recent_messages = history[-6:] if len(history) > 6 else history
    context = []
    
    for msg in recent_messages:
        if msg["role"] == "user" and len(msg["content"]) > 10:
            context.append(msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"])
    
    return " | ".join(context)

async def generate_business_plan_artifact(session_data, conversation_history):
    """Generate comprehensive business plan artifact with deep research"""
    
    # Conduct comprehensive research for business plan
    industry = session_data.get('industry', 'general business')
    location = session_data.get('location', 'United States')
    
    current_year = datetime.now().year
    previous_year = current_year - 1
    
    print(f"🔍 Conducting deep research for {industry} business in {location}")
    
    # Multiple research queries for comprehensive analysis
    market_research = await conduct_web_search(f"market analysis {industry} {location} {previous_year}")
    competitor_research = await conduct_web_search(f"top competitors {industry} business model analysis {previous_year}")
    industry_trends = await conduct_web_search(f"{industry} industry trends opportunities {previous_year}")
    financial_benchmarks = await conduct_web_search(f"{industry} financial benchmarks startup costs {previous_year}")
    
    business_plan_prompt = f"""
    Generate a comprehensive, detailed business plan based on the following conversation history and extensive research:
    
    Session Data: {json.dumps(session_data, indent=2)}
    
    Deep Research Conducted:
    Market Analysis: {market_research}
    Competitor Analysis: {competitor_research}
    Industry Trends: {industry_trends}
    Financial Benchmarks: {financial_benchmarks}
    
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
    
    Include a note at the beginning that this business plan incorporates deep research and market analysis to provide comprehensive insights beyond what was discussed in the questionnaire.
    
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
    
    current_year = datetime.now().year
    previous_year = current_year - 1
    
    vendor_research = await conduct_web_search(f"best business tools vendors {industry} {business_type} {previous_year}")
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