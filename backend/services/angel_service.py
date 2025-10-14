from openai import AsyncOpenAI
import os
import json
import re
from datetime import datetime
from utils.constant import ANGEL_SYSTEM_PROMPT

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Web search throttling
web_search_count = 0
web_search_reset_time = datetime.now()

def should_conduct_web_search():
    """Throttle web searches to prevent excessive API calls"""
    global web_search_count, web_search_reset_time
    
    # Reset counter every 10 seconds for faster reset during implementation
    if (datetime.now() - web_search_reset_time).seconds > 10:
        web_search_count = 0
        web_search_reset_time = datetime.now()
    
    # Allow maximum 2 web searches per 10 seconds for better performance
    if web_search_count >= 2:
        return False
    
    web_search_count += 1
    return True

TAG_PROMPT = """CRITICAL: You MUST include a machine-readable tag in EVERY response that contains a question. Use this exact format:
[[Q:<PHASE>.<NN>]] 

Examples:
- [[Q:KYC.01]] What's your name?
- [[Q:KYC.02]] What is your preferred communication style?
- [[Q:BUSINESS_PLAN.01]] What is your business idea?
- [[Q:BUSINESS_PLAN.19]] What is your revenue model?
- [[Q:BUSINESS_PLAN.20]] How will you market your business?

IMPORTANT RULES:
1. The tag must be at the beginning of your question, before any other text
2. Question numbers must be sequential and correct for the current phase
3. For BUSINESS_PLAN phase, questions should be numbered 01 through 46
4. NEVER jump backwards in question numbers (e.g., from 19 to 10)
5. If you're continuing a conversation, increment the question number appropriately

FAILURE TO INCLUDE CORRECT TAGS WILL BREAK THE SYSTEM. ALWAYS include the correct sequential tag before asking any question.

FORMATTING REQUIREMENT: Always use structured format for questions - NEVER paragraph format!"""

WEB_SEARCH_PROMPT = """You have access to web search capabilities, but use them VERY SPARINGLY during Implementation phase.

IMPLEMENTATION PHASE RULES:
• Use web search VERY SPARINGLY - maximum 1 search per response
• Focus on delivering quick, practical implementation steps
• Users expect fast responses during implementation (3-5 seconds max)
• Only search for the most critical information gaps
• AVOID multiple web searches - they cause delays

WEB SEARCH GUIDELINES:
• When web search results are provided, you MUST include them in your response immediately
• Use previous calendar year for search queries (e.g., "2024" instead of "2023")
• Provide comprehensive answers based on the research findings
• Do not ask the user to wait or send another message - deliver results immediately
• Include specific details from the research in your response
• Do not just say "I'm conducting research" - provide the actual research results

To use web search, include in your response: WEBSEARCH_QUERY: [your search query]"""

def is_draft_or_support_response(response_text: str) -> bool:
    """Check if response is a draft or support command response"""
    # First check if this is a verification/summary (NOT a draft)
    verification_indicators = [
        "Does this look accurate",
        "Does this look correct",
        "Is this accurate",
        "Verification:",
        "Here's what I've captured so far"
    ]
    
    # If it's a verification message, it's NOT a draft
    if any(indicator in response_text for indicator in verification_indicators):
        return False
    
    # Check for actual draft/support indicators
    draft_indicators = [
        "Here's a draft for you:",
        "Here's a draft based on what you've shared",
        "Let's work through this together",
        "Here's a refined version of your thoughts",
        "I'll create additional content for you"
    ]
    return any(indicator in response_text for indicator in draft_indicators)

def is_moving_to_next_question(response_text: str) -> bool:
    """Check if response is transitioning to next question (should NOT show buttons)"""
    response_lower = response_text.lower()
    
    # FIRST: Check if this is a Draft/Support/Scrapping response
    # These should NEVER be considered as "moving to next question"
    draft_or_support_indicators = [
        "here's a draft for you:",
        "here's a draft based on",
        "let's work through this together",
        "here's a refined version",
        "i'll create additional content"
    ]
    
    if any(indicator in response_lower for indicator in draft_or_support_indicators):
        # This is a draft/support response - should ALWAYS show buttons
        return False
    
    # Patterns that indicate moving to next question
    transition_patterns = [
        "let's move forward",
        "let's move on",
        "let's move to the next",
        "let's continue",
        "moving on to",
        "ready to move on",
        "let's proceed",
        "moving forward"
    ]
    
    # Check if response has transition pattern
    has_transition = any(pattern in response_lower for pattern in transition_patterns)
    
    # Check if asking a new question (question mark near the end)
    lines = response_text.split('\n')
    last_lines = '\n'.join(lines[-5:])  # Check last 5 lines
    has_question_at_end = "?" in last_lines
    
    # It's moving to next question if has transition AND question at end
    return has_transition and has_question_at_end

async def should_show_accept_modify_buttons(ai_response: str, user_last_input: str = "") -> dict:
    """Determine if Accept/Modify buttons should be shown"""
    user_input_lower = user_last_input.lower().strip()
    
    # Check if user explicitly requested Draft, Support, or Scrapping
    command_keywords = ["draft", "support", "scrapping", "scraping", "draft more"]
    is_command_request = user_input_lower in command_keywords
    
    # Check if response is a draft/support response
    is_draft_response = is_draft_or_support_response(ai_response)
    
    # Check if response is moving to next question
    is_next_question = is_moving_to_next_question(ai_response)
    
    # Show buttons ONLY if it's a command response AND not moving to next question
    should_show = (is_command_request or is_draft_response) and not is_next_question
    
    print(f"🔍 Button Detection:")
    print(f"  - User input: '{user_last_input[:50]}...'")
    print(f"  - Is command request: {is_command_request}")
    print(f"  - Is draft response: {is_draft_response}")
    print(f"  - Is next question: {is_next_question}")
    print(f"  - Should show buttons: {should_show}")
    
    return {
        "show_buttons": should_show,
        "content_length": len(ai_response)
    }

async def conduct_web_search(query):
    """Conduct web search using OpenAI's web search tool with progress indication"""
    try:
        # Check if we should conduct web search (throttling)
        if not should_conduct_web_search():
            print(f"🚫 Web search throttled - returning immediately. Query: {query[:50]}...")
            return "I'll provide guidance based on my existing knowledge to ensure fast response."
        
        print(f"🔍 Conducting web search: {query}")
        
        # Limit query length to prevent excessive API calls
        if len(query) > 80:  # Further reduced to 80 characters for faster processing
            query = query[:80] + "..."
        
        # Use a faster, more efficient approach with shorter timeout
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Use faster model for web search
            messages=[{
                "role": "user", 
                "content": f"Search for current information about: {query}. Provide a concise summary of key findings in 1 sentence."
            }],
            temperature=0.1,  # Lower temperature for more focused results
            max_tokens=50,  # Further reduced token limit for faster processing
            timeout=3.0  # 3 second timeout for faster response
        )
        
        # Extract search results from response
        search_results = response.choices[0].message.content
        print(f"✅ Web search completed for: {query[:50]}...")
        return search_results
    
    except Exception as e:
        print(f"❌ Web search error: {e}")
        return "I'll provide guidance based on my existing knowledge."

def trim_conversation_history(history, max_messages=10):
    """Trim conversation history to prevent context from growing too large"""
    if len(history) <= max_messages:
        return history
    
    # Keep the most recent messages
    return history[-max_messages:]

def format_response_structure(reply):
    """Format AI responses to use proper structured format instead of paragraph form"""
    
    formatted_reply = reply
    
    # Check if this should be a dropdown question (Yes/No or multiple choice)
    is_yes_no_question = ("yes" in formatted_reply.lower() and "no" in formatted_reply.lower() and 
                         any(phrase in formatted_reply.lower() for phrase in ["have you", "do you", "are you", "would you"]))
    
    is_work_situation_question = "work situation" in formatted_reply.lower()
    
    is_multiple_choice_question = ("•" in formatted_reply or "○" in formatted_reply or 
                                  any(option in formatted_reply.lower() for option in ["full-time employed", "part-time", "student", "unemployed"]))
    
    # For dropdown questions, remove the options from the message
    if is_yes_no_question:
        # Remove Yes/No options
        formatted_reply = re.sub(r'\n\n• Yes\n• No', '', formatted_reply)
        formatted_reply = re.sub(r'\n• Yes\n• No', '', formatted_reply)
        formatted_reply = re.sub(r'\n\nYes / No', '', formatted_reply)
        formatted_reply = re.sub(r'\nYes / No', '', formatted_reply)
    
    elif is_work_situation_question:
        # Remove work situation options
        work_options_pattern = r'\n\n• Full-time employed\n• Part-time\n• Student\n• Unemployed\n• Self-employed/freelancer\n• Other'
        formatted_reply = re.sub(work_options_pattern, '', formatted_reply)
        
        # Also handle single-line format
        work_options_single_pattern = r'\n• Full-time employed\n• Part-time\n• Student\n• Unemployed\n• Self-employed/freelancer\n• Other'
        formatted_reply = re.sub(work_options_single_pattern, '', formatted_reply)
    
    elif is_multiple_choice_question and not is_yes_no_question:
        # Remove bullet point options for other multiple choice questions
        # Pattern: "Question?\n\n• Option1\n• Option2\n• Option3"
        multi_choice_pattern = r'([^?]+\?)\s*\n\n(• [^\n]+(?:\n• [^\n]+)*)'
        formatted_reply = re.sub(multi_choice_pattern, r'\1', formatted_reply)
        
        # Also handle single-line format
        multi_choice_single_pattern = r'([^?]+\?)\s*\n(• [^\n]+(?:\n• [^\n]+)*)'
        formatted_reply = re.sub(multi_choice_single_pattern, r'\1', formatted_reply)
        
        # Handle circle bullets (○) - remove these options too
        circle_choice_pattern = r'([^?]+\?)\s*\n\n(○ [^\n]+(?:\n○ [^\n]+)*)'
        formatted_reply = re.sub(circle_choice_pattern, r'\1', formatted_reply)
        
        # Also handle single-line format for circles
        circle_choice_single_pattern = r'([^?]+\?)\s*\n(○ [^\n]+(?:\n○ [^\n]+)*)'
        formatted_reply = re.sub(circle_choice_single_pattern, r'\1', formatted_reply)
    
    # Specific formatting for work situation question (if not already handled)
    if "work situation" in formatted_reply.lower() and "?" in formatted_reply and not is_work_situation_question:
        # Pattern: "What's your current work situation? Full-time employed Part-time Student Unemployed Self-employed/freelancer Other"
        work_pattern = r'([^?]+\?)\s+(Full-time employed\s+Part-time\s+Student\s+Unemployed\s+Self-employed/freelancer\s+Other)'
        formatted_reply = re.sub(work_pattern, 
            r'\1\n\n• Full-time employed\n• Part-time\n• Student\n• Unemployed\n• Self-employed/freelancer\n• Other', 
            formatted_reply)
    
    # Specific formatting for business before question
    if "business before" in formatted_reply.lower() and "?" in formatted_reply:
        # Pattern: "Have you started a business before? Yes / No"
        business_pattern = r'([^?]+\?)\s+(Yes\s*/\s*No)'
        formatted_reply = re.sub(business_pattern, r'\1\n\n• Yes\n• No', formatted_reply)
    
    # General pattern for Yes/No questions (if not already handled)
    if not is_yes_no_question:
        # Pattern: "Question? Yes / No" or "Question? Yes/No"
        yes_no_pattern = r'([^?]+\?)\s+(Yes\s*/\s*No)'
        formatted_reply = re.sub(yes_no_pattern, r'\1\n\n• Yes\n• No', formatted_reply)
    
    # General pattern for multiple choice questions (if not already handled)
    if not is_multiple_choice_question:
        # Pattern: "Question? Option1 Option2 Option3 Option4"
        multi_choice_pattern = r'([^?]+\?)\s+([A-Za-z\s]+(?:employed|time|Student|Unemployed|freelancer|Other)[^?]*)'
        formatted_reply = re.sub(multi_choice_pattern, 
            lambda m: f"{m.group(1)}\n\n• {m.group(2).replace(' ', ' • ')}", 
            formatted_reply)
    
    # Convert circle bullets to regular bullets for consistency
    formatted_reply = re.sub(r'○\s*', '• ', formatted_reply)
    
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
            
            # Check if we're jumping ahead or backwards
            if "BUSINESS_PLAN." in asked_q:
                last_q_num = int(asked_q.split(".")[1])
                
                print(f"🔍 DEBUG - Question sequence check: last_q={last_q_num}, current_q={current_q_num}")
                
                # Handle jumping ahead (skipping questions)
                if current_q_num > last_q_num + 1:
                    print(f"⚠️ WARNING: Jumping ahead from question {last_q_num} to {current_q_num}")
                    # Force back to next sequential question
                    next_q = f"BUSINESS_PLAN.{last_q_num + 1:02d}"
                    reply = re.sub(r'\[\[Q:BUSINESS_PLAN\.\d+\]\]', f'[[Q:{next_q}]]', reply)
                    print(f"🔧 Corrected to: {next_q}")
                
                # Handle jumping backwards (going to previous questions)
                elif current_q_num < last_q_num:
                    print(f"⚠️ WARNING: Jumping backwards from question {last_q_num} to {current_q_num}")
                    # Force to next sequential question (don't go backwards)
                    next_q = f"BUSINESS_PLAN.{last_q_num + 1:02d}"
                    reply = re.sub(r'\[\[Q:BUSINESS_PLAN\.\d+\]\]', f'[[Q:{next_q}]]', reply)
                    print(f"🔧 Corrected backwards jump to: {next_q}")
                
                # Log normal progression
                elif current_q_num == last_q_num + 1:
                    print(f"✅ Normal progression: {last_q_num} → {current_q_num}")
                
                # Handle staying on the same question (shouldn't happen)
                elif current_q_num == last_q_num:
                    print(f"⚠️ WARNING: Staying on same question {current_q_num}")
                    # Force to next question
                    next_q = f"BUSINESS_PLAN.{last_q_num + 1:02d}"
                    reply = re.sub(r'\[\[Q:BUSINESS_PLAN\.\d+\]\]', f'[[Q:{next_q}]]', reply)
                    print(f"🔧 Forced progression to: {next_q}")

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
        # Only trigger for specific verification patterns, not general responses
        verification_keywords = [
            "does this look accurate to you",
            "does this look correct to you", 
            "is this accurate to you",
            "is this correct to you",
            "please let me know where you'd like to modify"
        ]
        
        # Only add Accept/Modify if it's explicitly a verification request
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
    
    # Don't suggest draft in KYC phase
    if session_data and session_data.get("current_phase") == "KYC":
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
        
        # Check for various tip patterns that might already exist
        tip_patterns = [
            "💡 Quick Tip:",
            "💡 **Quick Tip**:",
            "💡 **Pro Tip**:",
            "💡 Quick tip:",
            "💡 **Quick tip**:",
            "💡 **Pro tip**:",
            "Quick Tip:",
            "**Quick Tip**:",
            "**Pro Tip**:",
            "Quick tip:",
            "**Quick tip**:",
            "**Pro tip**:"
        ]
        
        has_existing_tip = any(pattern in reply for pattern in tip_patterns)
        
        if user_has_relevant_info and not has_existing_tip:
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
    
    # Don't add support guidance in KYC phase
    if session_data and session_data.get("current_phase") == "KYC":
        return reply
    
    # Only add support guidance if not already present in the reply
    tip_patterns = [
        "💡 Quick Tip:",
        "💡 **Quick Tip**:",
        "💡 **Pro Tip**:",
        "💡 Quick tip:",
        "💡 **Quick tip**:",
        "💡 **Pro tip**:",
        "Quick Tip:",
        "**Quick Tip**:",
        "**Pro Tip**:",
        "Quick tip:",
        "**Quick tip**:",
        "**Pro tip**:",
        "🎯 Areas Where You May Need Additional Support:"
    ]
    
    has_existing_guidance = any(pattern in reply for pattern in tip_patterns)
    
    if has_existing_guidance:
        return reply
    
    support_areas = identify_support_areas(session_data, history)
    
    if support_areas and len(support_areas) > 0:
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
        # Pattern: Yes/No questions without proper formatting
        (r'([^?]+\?)\s+(Yes\s*/\s*No)', r'\1\n\n• Yes\n• No'),
        # Pattern: Question without proper line breaks
        (r'([^?]+\?)\s+([A-Z][^?]+)', r'\1\n\n\2'),
        # Pattern: Multiple choice options without proper formatting
        (r'([^?]+\?)\s+([A-Z][^?]+(?:employed|time|Student|Unemployed|freelancer|Other)[^?]*)', 
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
    
    # Check if this is a command response (Draft, Support, Scrapping) - don't inject tags for these
    # Also includes verification messages that should stay on same question
    command_indicators = [
        "Here's a draft for you",
        "Here's a draft based on what you've shared",
        "Let's work through this together",
        "Here's a refined version of your thoughts",
        "I'll create additional content for you",
        "Verification:",
        "Here's what I've captured so far",
        "Does this look accurate",
        "Does this look correct"
    ]
    
    if any(indicator in reply for indicator in command_indicators):
        # This is a command response, don't inject a tag - stay on current question
        return reply
    
    # Determine the question number to inject
    # When AI asks a new question without a tag, inject the NEXT question number
    current_phase = "KYC"  # Default
    question_num = "01"    # Default
    
    if session_data:
        current_phase = session_data.get("current_phase", "KYC")
        asked_q = session_data.get("asked_q", "KYC.01")
        if "." in asked_q:
            phase, num = asked_q.split(".")
            current_phase = phase
            # INCREMENT to get the NEXT question number (since user just answered current question)
            try:
                next_num = int(num) + 1
                question_num = f"{next_num:02d}"  # Format as 01, 02, 03, etc.
            except (ValueError, TypeError):
                question_num = num  # Fallback to current if parsing fails
    
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

async def handle_kyc_completion(session_data, history):
    """Handle the transition from KYC completion to Business Plan phase"""
    
    # Return the completion message and trigger transition
    acknowledgment = """That's fantastic! Your proactive approach will help ensure we make the most of our time together and that you get the guidance you need when you need it.

🎉 **Congratulations! You've completed your entrepreneurial profile!** 🎉

Here's what I've learned about you and your goals:

• You're ready to take a proactive approach to building your business
• You've shared valuable insights about your experience, goals, and preferences
• You're prepared to dive deep into the business planning process

Now we're moving into the exciting Business Planning phase! This is where we'll dive deep into every aspect of your business idea. I'll be asking detailed questions about your product, market, finances, and strategy.

During this phase, I'll be conducting research in the background to provide you with industry insights, competitive analysis, and market data to enrich your business plan. Don't worry - this happens automatically and securely.

As we go through each question, I'll provide both supportive encouragement and constructive coaching to help you think through each aspect thoroughly. Remember, this comprehensive approach ensures your final business plan is detailed and provides you with a strong starting point of information that will help you launch your business. The more detailed answers you provide, the better I can help support you to bring your business to life.

Let's build the business of your dreams together!

*'The way to get started is to quit talking and begin doing.' - Walt Disney*

Ready to dive into your business planning?"""
    
    return {
        "reply": acknowledgment,
        "transition_phase": "KYC_TO_BUSINESS_PLAN",
        "patch_session": {
            "current_phase": "BUSINESS_PLAN",
            "asked_q": "BUSINESS_PLAN.01",
            "answered_count": 0
        }
    }

async def handle_business_plan_completion(session_data, history):
    """Handle the transition from Business Plan completion to Roadmap phase"""
    
    # Generate comprehensive business plan summary
    business_plan_summary = await generate_business_plan_summary(session_data, history)
    
    # Create the transition message
    transition_message = f"""🎉 **CONGRATULATIONS! Planning Champion Award** 🎉

You've successfully completed your comprehensive business plan! This is a significant milestone in your entrepreneurial journey.

**"Success is not final; failure is not fatal: it is the courage to continue that counts."** – Winston Churchill

---

## 📋 **Comprehensive Business Plan Recap**

{business_plan_summary}

---

## 🎯 **What's Next: Roadmap Generation**

Based on your detailed business plan, I will now generate a comprehensive, actionable launch roadmap that translates your plan into explicit, chronological tasks. This roadmap will include:

• **Legal Formation** - Business structure, licensing, permits
• **Financial Planning** - Funding strategies, budgeting, accounting setup
• **Product & Operations** - Supply chain, equipment, operational processes
• **Marketing & Sales** - Brand positioning, customer acquisition, sales processes
• **Full Launch & Scaling** - Go-to-market strategy, growth planning

The roadmap will be tailored specifically to your business, industry, and location, with research-backed recommendations and local service provider options.

---

## 🚀 **Ready to Move Forward?**

Please review your business plan summary above. If everything looks accurate and complete, you can:

**✅ Approve Plan** - Proceed to roadmap generation
**🔄 Revisit Plan** - Modify any aspects that need adjustment

What would you like to do?"""

    return {
        "reply": transition_message,
        "web_search_status": {"is_searching": False, "query": None},
        "immediate_response": None,
        "transition_phase": "PLAN_TO_ROADMAP",
        "business_plan_summary": business_plan_summary
    }

async def generate_business_plan_summary(session_data, history):
    """Generate a comprehensive summary of the business plan"""
    
    # Extract key information from session data and history
    summary_sections = []
    
    # Business Foundation
    if session_data.get("business_idea_brief"):
        summary_sections.append(f"**Business Idea:** {session_data.get('business_idea_brief')}")
    
    if session_data.get("business_type"):
        summary_sections.append(f"**Business Type:** {session_data.get('business_type')}")
    
    if session_data.get("industry"):
        summary_sections.append(f"**Industry:** {session_data.get('industry')}")
    
    if session_data.get("location"):
        summary_sections.append(f"**Location:** {session_data.get('location')}")
    
    if session_data.get("motivation"):
        summary_sections.append(f"**Motivation:** {session_data.get('motivation')}")
    
    # Extract additional information from conversation history
    user_responses = [msg.get('content', '') for msg in history if msg.get('role') == 'user']
    conversation_text = ' '.join(user_responses)
    
    # Generate AI-powered summary
    summary_prompt = f"""
    Create a comprehensive business plan summary based on the following information:
    
    Session Data: {session_data}
    Conversation History: {conversation_text[:2000]}  # Limit to avoid token limits
    
    Provide a structured summary that includes:
    1. Business Overview
    2. Target Market
    3. Products/Services
    4. Business Model
    5. Key Strategies
    6. Financial Considerations
    7. Next Steps
    
    Make it professional and comprehensive, highlighting the key decisions and milestones achieved.
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.6,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating business plan summary: {e}")
        return "Business plan summary generation in progress..."

def provide_critiquing_feedback(user_msg, session_data, history):
    """
    Provide constructive critique and challenging feedback to push for deeper thinking
    """
    # Don't critique simple yes/no answers or very short responses to simple questions
    if not user_msg or len(user_msg.strip()) < 5:
        return None
    
    # Check for vague or unrealistic answers only for complex questions
    vague_indicators = ["maybe", "probably", "i think", "not sure", "don't know", "maybe", "possibly"]
    if any(indicator in user_msg.lower() for indicator in vague_indicators) and len(user_msg.strip()) > 50:
        return {
            "reply": f"I notice some uncertainty in your response. Let me challenge you to think deeper: What specific research have you done to support this? What are the concrete steps you're considering? What potential obstacles do you foresee, and how would you address them?",
            "web_search_status": {"is_searching": False, "query": None, "completed": False}
        }
    
    # Check for unrealistic assumptions
    unrealistic_indicators = ["easy", "simple", "quick", "fast", "guaranteed", "definitely will work"]
    if any(indicator in user_msg.lower() for indicator in unrealistic_indicators) and len(user_msg.strip()) > 50:
        return {
            "reply": f"While I appreciate your confidence, I want to challenge some assumptions here. What makes you think this will be [easy/simple/quick]? What data or experience supports this timeline? What's your contingency plan if things don't go as expected?",
            "web_search_status": {"is_searching": False, "query": None, "completed": False}
        }
    
    return None

def validate_question_answer(user_msg, session_data, history):
    """
    Enhanced validation with critiquing behaviors - challenge superficial answers
    and push for deeper thinking and specificity.
    Validate that user is not trying to skip questions in KYC and Business Plan phases
    """
    if not session_data:
        return None
    
    current_phase = session_data.get("current_phase", "")
    asked_q = session_data.get("asked_q", "")
    
    # Don't validate during initial startup (when asked_q is empty or initial)
    if not asked_q or asked_q in ["", "KYC.01", "BUSINESS_PLAN.01"]:
        return None
    
    # Only validate for KYC and Business Plan phases
    if current_phase not in ["KYC", "BUSINESS_PLAN"]:
        return None
    
    # Extract content from user_msg (could be dict or string)
    if isinstance(user_msg, dict):
        user_content = user_msg.get("content", "")
    else:
        user_content = str(user_msg)
    
    # Check if user is trying to use commands to skip questions
    user_msg_lower = user_content.lower().strip()
    
    # Commands that are allowed (these don't skip questions, they help answer them)
    # In KYC phase, disable all helper commands to force direct answers
    if current_phase == "KYC":
        blocked_commands = ["draft", "support", "scrapping:", "kickstart", "who do i contact?"]
        
        # Block these commands in KYC phase
        if any(user_msg_lower.startswith(cmd) for cmd in blocked_commands):
            return {
                "reply": f"""I understand you'd like to use helper tools, but during the KYC phase, it's important that you provide direct answers to help me understand your background and goals.

Please provide a direct answer to the current question. This will help me personalize your experience and provide the most relevant guidance for your specific situation.

The helper tools (Draft, Support, Scrapping, Kickstart, Contact) will be available in the Business Planning phase where they can be more helpful for complex business questions.

For now, please share your thoughts directly about the current question.""",
                "web_search_status": {"is_searching": False, "query": None, "completed": False}
            }
    else:
        # In other phases, allow these commands
        allowed_commands = ["draft", "support", "scrapping:", "kickstart", "who do i contact?"]
        
        # If user is using an allowed command, let them proceed
        if any(user_msg_lower.startswith(cmd) for cmd in allowed_commands):
            return None
    
    # Check for attempts to skip or manipulate the conversation
    skip_indicators = [
        "skip", "next", "move on", "continue", "go to next", "next question",
        "i don't want to answer", "i'll answer later", "not now", "maybe later",
        "i'm done", "finished", "complete", "that's enough", "no more questions"
    ]
    
    if any(indicator in user_msg_lower for indicator in skip_indicators):
        # Get the current question context
        current_question_num = "1"
        if "." in asked_q:
            try:
                current_question_num = asked_q.split(".")[1]
            except:
                pass
        
        # Create phase-specific message
        if current_phase == "KYC":
            help_message = """Please provide a direct answer to the current question. This will help me personalize your experience and provide the most relevant guidance for your specific situation."""
        else:
            help_message = """If you're unsure about how to answer, you can use:
- **Support** - for guided help with the question
- **Draft** - for me to help create an answer based on what you've shared so far"""
        
        return {
            "reply": f"""I understand you'd like to move forward, but it's important that we complete each question to ensure I can provide you with the best possible guidance.

We're currently on question {current_question_num} of the {current_phase} phase. Each question is designed to help me understand your specific situation and provide personalized advice.

Please provide an answer to the current question so we can continue building your comprehensive business plan together. Your detailed responses will help me tailor the guidance specifically for your needs.

{help_message}

Let's continue with the current question.""",
            "web_search_status": {"is_searching": False, "query": None, "completed": False}
        }
    
    # Check if user is asking clarifying questions about the current question (these are allowed)
    clarifying_questions = [
        "what question", "what is the question", "what do you want to know", "what should i answer",
        "what are you asking", "what is this question about", "can you repeat the question",
        "what do you need to know", "what information do you need", "what should i tell you"
    ]
    
    if any(clarifying_question in user_msg_lower for clarifying_question in clarifying_questions):
        # Allow clarifying questions - these help users understand what to answer
        return None
    
    # Check if user is trying to ask unrelated questions instead of answering
    unrelated_question_indicators = ["what is ai", "tell me about", "explain", "how does", "can you tell me about"]
    
    if user_msg_lower.endswith("?") and any(indicator in user_msg_lower for indicator in unrelated_question_indicators):
        # Create phase-specific message
        if current_phase == "KYC":
            help_message = """Please provide a direct answer to help me understand your situation better."""
        else:
            help_message = """If you need help with the current question, you can use:
- **Support** - for guided help with the question
- **Draft** - for me to help create an answer based on what you've shared so far"""
        
        return {
            "reply": f"""I appreciate your question! However, right now we're in the {current_phase} phase where I'm gathering information about you and your business to provide personalized guidance.

I'd be happy to answer your question once we complete the current question. For now, please provide an answer to help me understand your situation better.

{help_message}

Let's focus on answering the current question first.""",
            "web_search_status": {"is_searching": False, "query": None, "completed": False}
        }
    
    # Check if user is providing rating responses to non-rating questions
    if current_phase == "KYC":
        # Check if this looks like a rating response (numbers separated by commas)
        rating_pattern = r'^\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+$'
        if re.match(rating_pattern, user_content.strip()):
            # Only allow rating responses for KYC.07 (skills rating question)
            if asked_q != "KYC.07":
                return {
                    "reply": f"""I see you've provided a rating response, but the current question is asking about something different.

We're currently on question {asked_q.split('.')[1] if '.' in asked_q else 'unknown'} which asks: "{asked_q.replace('KYC.', '')}"

Please provide an answer that directly addresses the current question instead of rating responses.""",
                    "web_search_status": {"is_searching": False, "query": None, "completed": False}
                }
    
    # Check for very short or empty responses that might indicate skipping
    if len(user_content.strip()) < 3 and user_msg_lower not in ["yes", "no", "y", "n", "ok", "okay"]:
        # Different messages for KYC vs other phases
        if current_phase == "KYC":
            return {
                "reply": f"""I need a bit more information to help you effectively. Please provide a more detailed answer to the current question.

The more information you share, the better I can tailor my guidance to your specific situation and needs.

Please provide a more detailed response to continue.""",
                "web_search_status": {"is_searching": False, "query": None, "completed": False}
            }
        else:
            return {
                "reply": f"""I need a bit more information to help you effectively. Please provide a more detailed answer to the current question.

The more information you share, the better I can tailor my guidance to your specific situation and needs.

If you're unsure how to answer, you can use:
- **Support** - for guided help with the question
- **Draft** - for me to help create an answer based on what you've shared so far

Please provide a more detailed response to continue.""",
                "web_search_status": {"is_searching": False, "query": None, "completed": False}
            }
    
    return None

def validate_session_state(session_data, history):
    """Validate session state integrity to prevent question skipping"""
    if not session_data:
        return None
    
    current_phase = session_data.get("current_phase", "")
    asked_q = session_data.get("asked_q", "")
    answered_count = session_data.get("answered_count", 0)
    
    # Don't validate during initial startup (when asked_q is empty or initial)
    if not asked_q or asked_q in ["", "KYC.01", "BUSINESS_PLAN.01"]:
        return None
    
    # Only validate for KYC and Business Plan phases
    if current_phase not in ["KYC", "BUSINESS_PLAN"]:
        return None
    
    # Calculate expected answered count based on history
    expected_answered_count = len([pair for pair in history if pair.get("answer", "").strip()])
    
    # Check if answered_count is significantly behind (indicating skipped questions)
    # Only trigger if there's a major discrepancy (more than 2 questions behind)
    if answered_count < expected_answered_count - 2:
        # Create phase-specific message
        if current_phase == "KYC":
            help_message = """Please provide a complete answer to the current question so we can continue building your comprehensive business plan."""
        else:
            help_message = """If you need help with the current question, you can use:
- **Support** - for guided help with the question
- **Draft** - for me to help create an answer based on what you've shared so far"""
        
        return {
            "reply": f"""I notice there might be a discrepancy in our conversation history. To ensure I can provide you with the most accurate and personalized guidance, we need to make sure we've properly addressed all questions.

We're currently in the {current_phase} phase. Please provide a complete answer to the current question so we can continue building your comprehensive business plan.

Your detailed responses are essential for creating a tailored business strategy that addresses your specific needs and goals.

{help_message}

Let's continue with the current question.""",
            "web_search_status": {"is_searching": False, "query": None, "completed": False}
        }
    
    # Validate that asked_q is in the correct format and sequence
    if current_phase == "KYC":
        if not asked_q.startswith("KYC.") and asked_q != "KYC.19_ACK":
            return {
                "reply": f"""I need to ensure we're following the proper KYC sequence. Please provide an answer to the current KYC question so we can continue systematically building your business profile.

Each question in the KYC phase is designed to help me understand your background, experience, and goals. Skipping questions would prevent me from providing you with the most relevant and personalized guidance.

Please provide a detailed answer to the current question. This will help me personalize your experience and provide the most relevant guidance for your specific situation.

Let's continue with the current KYC question.""",
                "web_search_status": {"is_searching": False, "query": None, "completed": False}
            }
    
    elif current_phase == "BUSINESS_PLAN":
        if not asked_q.startswith("BUSINESS_PLAN."):
            return {
                "reply": f"""I need to ensure we're following the proper Business Plan sequence. Please provide an answer to the current business planning question so we can continue systematically developing your business strategy.

Each question in the Business Plan phase is designed to help create a comprehensive and actionable business plan tailored to your specific situation. Skipping questions would result in an incomplete plan that doesn't address all the necessary aspects of your business.

Please provide a detailed answer to the current question.

If you need help, you can use:
- **Support** - for guided help with the question
- **Draft** - for me to help create an answer based on what you've shared so far

Let's continue with the current business planning question.""",
                "web_search_status": {"is_searching": False, "query": None, "completed": False}
            }
    
    return None

async def get_angel_reply(user_msg, history, session_data=None):
    import time
    start_time = time.time()
    
    # Get user name from session data, fallback to generic greeting
    user_name = session_data.get("user_name", "there") if session_data else "there"
    
    # KYC completion check removed - now triggered immediately after final answer
    
    # Validate that user is not trying to skip questions
    validation_result = validate_question_answer(user_msg, session_data, history)
    if validation_result:
        return validation_result
    
    # Debug logging for session state
    if session_data:
        print(f"🔍 DEBUG - Session State: phase={session_data.get('current_phase')}, asked_q={session_data.get('asked_q')}, answered_count={session_data.get('answered_count')}")
    
    # Validate session state integrity
    session_validation = validate_session_state(session_data, history)
    if session_validation:
        print(f"🔍 DEBUG - Session validation triggered: {session_validation.get('reply', '')[:100]}...")
        return session_validation
    
    # Provide critiquing feedback for superficial or unrealistic answers
    if user_msg and user_msg.get("content"):
        critique_feedback = provide_critiquing_feedback(user_msg["content"], session_data, history)
        if critique_feedback:
            print(f"🔍 DEBUG - Critiquing feedback triggered: {critique_feedback.get('reply', '')[:100]}...")
            return critique_feedback
    
    # Define formatting instruction at the top to avoid UnboundLocalError
    # Get current phase and question info for Business Plan numbering
    current_phase = session_data.get("current_phase", "KYC") if session_data else "KYC"
    asked_q = session_data.get("asked_q", "KYC.01") if session_data else "KYC.01"
    
    # Calculate current question number for Business Plan phase
    # asked_q represents the CURRENT question being asked, not the next one
    question_number_display = ""
    if current_phase == "BUSINESS_PLAN" and "." in asked_q:
        try:
            current_num = int(asked_q.split(".")[1])
            question_number_display = f"Question {current_num}"
        except (ValueError, IndexError):
            question_number_display = ""
    
    FORMATTING_INSTRUCTION = f"""
CRITICAL FORMATTING RULES - FOLLOW EXACTLY:

1. ALWAYS start with a brief acknowledgment (1-2 sentences max)
2. Add a blank line for visual separation
3. {f"BUSINESS PLAN: Include '{question_number_display}' on its own line after acknowledgment and before question" if question_number_display else "Present the question in a clear, structured format"}
4. Present the question in a clear, structured format:

For YES/NO questions:
"That's great, {user_name}!
{chr(10) + question_number_display + chr(10) if question_number_display else ""}
Have you started a business before?
• Yes
• No"

For multiple choice questions:
"That's perfect, {user_name}!
{chr(10) + question_number_display + chr(10) if question_number_display else ""}
What's your current work situation?"

NOTE: Do NOT list option bullets in your message. The UI displays clickable option buttons.

For rating questions:
"That's helpful, {user_name}!
{chr(10) + question_number_display + chr(10) if question_number_display else ""}
How comfortable are you with business planning?
○ ○ ○ ○ ○
1  2  3  4  5"

For verification steps:
"That's excellent, {user_name}!

Here's what I've captured so far:
[Summary of information]

Does this look accurate to you? If not, please let me know where you'd like to modify and we'll work through this some more."

❌ NEVER LIST OPTIONS IN YOUR MESSAGE: 
"What's your current work situation? • Full-time • Part-time • Student..."
"Will your business be primarily: • Online • Brick-and-mortar • Mix of both"

✅ CORRECT - ASK CLEANLY WITHOUT OPTIONS: 
"What's your current work situation:"
"Will your business be primarily:"

CRITICAL: The UI displays option buttons automatically. Do NOT include option lists in your message text.

BUSINESS PLAN SPECIFIC RULES:
• Ask ONE question at a time in EXACT sequential order
{f"• CRITICAL: Include '{question_number_display}' on its own line after acknowledgment" if question_number_display else ""}
• After every 3-4 questions, provide verification step
• Wait for user acknowledgment before proceeding
• Never combine questions or skip verification steps
• Each question must be on its own line with proper spacing
• Use verification format: "Here's what I've captured so far: [summary]. Does this look accurate to you?"
• NEVER mold user answers into mission, vision, USP without explicit verification
• Do NOT list option bullets in your message - UI shows clickable buttons for multiple-choice questions
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
    
    # Handle empty input based on context
    if not user_msg.get("content") or user_msg["content"].strip() == "":
        # If we're revisiting business plan, continue with current question
        if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
            current_tag = session_data.get("asked_q", "BUSINESS_PLAN.01")
            if current_tag and current_tag.startswith("BUSINESS_PLAN."):
                # Generate the current question
                question_prompt = f"""
                Generate the business plan question for tag: {current_tag}
                
                Make sure to:
                1. Ask the appropriate business plan question for this tag
                2. Include the proper tag: [[Q:{current_tag}]]
                3. Use structured format with proper line breaks
                4. Provide context if this is a verification or continuation
                """
                
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": ANGEL_SYSTEM_PROMPT},
                        {"role": "system", "content": TAG_PROMPT},
                        {"role": "system", "content": FORMATTING_INSTRUCTION},
                        {"role": "user", "content": question_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                return response.choices[0].message.content
        
        # Default to "hi" for other cases
        user_msg["content"] = "hi"

    user_content = user_msg["content"].strip()
    print(f"🚀 Starting Angel reply generation for: {user_content[:50]}...")
    
    # KYC completion check moved to AFTER AI response generation
    
    # Check if Business Plan phase is complete (question 46 for full flow)
    if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        current_tag = session_data.get("asked_q", "")
        if current_tag and current_tag.startswith("BUSINESS_PLAN."):
            try:
                question_num = int(current_tag.split(".")[1])
                if question_num >= 46:  # Business Plan complete (restored to full 46 questions)
                    return await handle_business_plan_completion(session_data, history)
            except (ValueError, IndexError):
                pass
    
    # Handle Accept response for verification
    if user_content.lower() == "accept":
        # Check if we're in a verification flow
        if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
            # Move to next question in business plan
            current_tag = session_data.get("asked_q", "BUSINESS_PLAN.01")
            if current_tag and current_tag.startswith("BUSINESS_PLAN."):
                try:
                    current_num = int(current_tag.split(".")[1])
                    next_num = current_num + 1
                    next_tag = f"BUSINESS_PLAN.{next_num:02d}"
                    
                    # Check if we've reached the end of business plan questions
                    if next_num > 46:  # Business plan is complete (restored to full 46 questions)
                        # Business plan is complete, trigger completion
                        return await handle_business_plan_completion(session_data, history)
                    
                    # Generate next question
                    next_question_prompt = f"""
                    The user has accepted the verification for business plan question {current_tag}. 
                    Now move to the next business plan question: {next_tag}
                    
                    Generate the next business plan question in the sequence. Make sure to:
                    1. Acknowledge their acceptance briefly (1-2 sentences)
                    2. Ask the next sequential business plan question
                    3. Include the proper tag: [[Q:{next_tag}]]
                    4. Use structured format with proper line breaks
                    5. Make it feel like a natural continuation of the business planning process
                    """
                    
                    response = await client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": ANGEL_SYSTEM_PROMPT},
                            {"role": "system", "content": TAG_PROMPT},
                            {"role": "system", "content": FORMATTING_INSTRUCTION},
                            {"role": "user", "content": next_question_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    
                    # Return the response with session update info
                    return {
                        "reply": response.choices[0].message.content,
                        "patch_session": {
                            "asked_q": next_tag,
                            "answered_count": session_data.get("answered_count", 0) + 1
                        }
                    }
                except (ValueError, IndexError):
                    pass
        
        # For other cases, let the normal flow handle it
        # Don't return a fallback here - let the main AI generation handle the response
    
    # Add instruction for proper question formatting
    
    # Check if web search is needed based on session phase and content
    needs_web_search = False
    web_search_query = None
    competitor_research_requested = False
    
    # Check for WEBSEARCH_QUERY trigger from scrapping command
    if "WEBSEARCH_QUERY:" in user_content:
        needs_web_search = True
        web_search_query = user_content.split("WEBSEARCH_QUERY:")[1].strip()
        print(f"🔍 Web search triggered by scrapping command: {web_search_query}")
    
    elif session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        # Look for competitive analysis, market research, or vendor recommendation needs
        business_keywords = ["competitors", "market", "industry", "trends", "pricing", "vendors", "domain", "legal requirements"]
        if any(keyword in user_content.lower() for keyword in business_keywords):
            needs_web_search = True
            
            # Extract or generate search query with previous calendar year
            current_year = datetime.now().year
            previous_year = current_year - 1
            
            # ENHANCED COMPETITOR RESEARCH DETECTION
            competitor_keywords = ["competitors", "competition", "main competitors", "who are my competitors", "competing companies", "rival companies"]
            if any(keyword in user_content.lower() for keyword in competitor_keywords):
                competitor_research_requested = True
                web_search_query = f"main competitors in {session_data.get('industry', 'business')} industry {previous_year}"
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
        
        # ENHANCED COMPETITOR RESEARCH HANDLING
        if competitor_research_requested:
            # Extract business context for comprehensive competitor research
            business_context = extract_business_context_from_history(history)
            if session_data:
                business_context.update({
                    "industry": session_data.get("industry", ""),
                    "location": session_data.get("location", ""),
                    "business_name": session_data.get("business_name", ""),
                    "business_type": session_data.get("business_type", "")
                })
            
            # Conduct comprehensive competitor research
            competitor_research_result = await handle_competitor_research_request(user_content, business_context, history)
            
            if competitor_research_result.get("success"):
                search_results = f"\n\n🔍 **Comprehensive Competitor Research Results:**\n\n{competitor_research_result['analysis']}\n\n*Research conducted using {competitor_research_result['research_sources']} authoritative sources*"
            else:
                # Fallback to regular web search
                search_start = time.time()
                search_results = await conduct_web_search(web_search_query)
                search_time = time.time() - search_start
                print(f"🔍 Web search completed in {search_time:.2f} seconds")
                
                if search_results and "unable to conduct web research" not in search_results:
                    search_results = f"\n\nResearch Results:\n{search_results}"
        else:
            # Regular web search for non-competitor requests
            search_start = time.time()
            search_results = await conduct_web_search(web_search_query)
            search_time = time.time() - search_start
            print(f"🔍 Web search completed in {search_time:.2f} seconds")
            
            if search_results and "unable to conduct web research" not in search_results:
                search_results = f"\n\nResearch Results:\n{search_results}"
        
        # Update status to completed
        web_search_status = {"is_searching": False, "query": web_search_query, "completed": True}

    # Check if this is an Accept command - handle it specially
    if user_content.lower().strip() == "accept" and session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        print(f"🔧 Accept command detected - moving to next question")
        
        # Move to next question by incrementing the question counter
        current_tag = session_data.get("asked_q", "BUSINESS_PLAN.01")
        if "." in current_tag:
            phase, num = current_tag.split(".")
            next_num = str(int(num) + 1).zfill(2)
            next_tag = f"{phase}.{next_num}"
            
            # Update session data
            session_data["asked_q"] = next_tag
            session_data["answered_count"] = session_data.get("answered_count", 0) + 1
            
            # Generate the next question
            next_question = await generate_next_question(next_tag, session_data)
            
            return {
                "reply": next_question,
                "web_search_status": {"is_searching": False, "query": None, "completed": False},
                "immediate_response": None,
                "patch_session": {
                    "asked_q": next_tag,
                    "answered_count": session_data["answered_count"]
                }
            }
    
    # Check if this is a command that should not generate new questions
    is_command_response = user_content.lower() in ["draft", "support", "scrapping", "scraping", "draft more"] or user_content.lower().startswith("scrapping:")
    
    # Check if this is an "Accept" command from Support/Draft/Scrapping
    is_accept_command = user_content.lower().strip() == "accept"
    
    # Handle Accept command - treat as a regular answer to move to next question
    if is_accept_command and session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        print(f"✅ Accept command detected - treating as answer to move to next question")
        # Let it pass through to normal AI processing which will move to the next question
        # Don't bypass AI generation - we want to get the next question
        pass
    
    # For commands, bypass AI generation and provide direct responses
    elif is_command_response and session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        print(f"🔧 Command detected: {user_content.lower()} - bypassing AI generation to prevent question skipping")
        
        # Generate direct command response without AI
        if user_content.lower() == "draft":
            reply_content = await handle_draft_command("", history, session_data)
        elif user_content.lower().startswith("scrapping:"):
            notes = user_content[10:].strip()
            scrapping_result = await handle_scrapping_command("", notes, history, session_data)
            # Add show_accept_modify for scrapping responses
            scrapping_result["show_accept_modify"] = True
            # If web search is needed, let the main function handle it
            if scrapping_result.get("web_search_status", {}).get("is_searching"):
                needs_web_search = True
                web_search_query = scrapping_result["web_search_status"]["query"]
                reply_content = scrapping_result["reply"]
            else:
                return scrapping_result
        elif user_content.lower() in ["scrapping", "scraping"]:
            scrapping_result = await handle_scrapping_command("", "", history, session_data)
            # Add show_accept_modify for scrapping responses
            scrapping_result["show_accept_modify"] = True
            # If web search is needed, let the main function handle it
            if scrapping_result.get("web_search_status", {}).get("is_searching"):
                needs_web_search = True
                web_search_query = scrapping_result["web_search_status"]["query"]
                reply_content = scrapping_result["reply"]
            else:
                return scrapping_result
        elif user_content.lower() == "support":
            reply_content = await handle_support_command("", history, session_data)
        elif user_content.lower() == "draft more":
            reply_content = await handle_draft_more_command("", history, session_data)
        else:
            # Fallback to normal AI generation
            reply_content = "I understand you'd like to use a command. Please try again."
        
        # For command responses, ALWAYS show Accept/Modify buttons
        # Return the command response with button detection
        return {
            "reply": reply_content,
            "web_search_status": {"is_searching": False, "query": None, "completed": False},
            "immediate_response": None,
            "show_accept_modify": True  # Always show buttons for Draft/Support/Scrapping
        }
    
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
    
    # Add session context to help AI maintain state
    if session_data:
        current_phase = session_data.get("current_phase", "KYC")
        asked_q = session_data.get("asked_q", "KYC.01")
        answered_count = session_data.get("answered_count", 0)
        
        # Determine next question number
        next_question_num = "01"
        if "." in asked_q:
            try:
                current_num = int(asked_q.split(".")[1])
                next_question_num = f"{current_num + 1:02d}"
            except (ValueError, IndexError):
                pass
        
        # Calculate question number for display in session context
        next_q_display = ""
        if current_phase == "BUSINESS_PLAN":
            try:
                q_num = int(next_question_num)
                next_q_display = f"Question {q_num}"
            except (ValueError, TypeError):
                next_q_display = ""
        
        session_context = f"""
CURRENT SESSION STATE:
- Current Phase: {current_phase}
- Last Question Asked: {asked_q}
- Questions Answered: {answered_count}
- Next Question Should Be: {current_phase}.{next_question_num}

CRITICAL INSTRUCTIONS:
1. You must continue from where the user left off
2. Do NOT restart the phase or go back to earlier questions
3. The next question should be {current_phase}.{next_question_num}
4. Only ask ONE question at a time
5. Use the proper tag format: [[Q:{current_phase}.{next_question_num}]]
{f"6. YOU MUST include '{next_q_display}' on its own line in your response (after acknowledgment, before question)" if next_q_display else "6. Continue with the next sequential question"}
7. Do NOT ask about business plan drafting or other phases - stay in {current_phase} phase
8. Continue with the next sequential question in the {current_phase} phase
9. NEVER skip questions - ask them in exact sequential order
10. If user provides an answer, acknowledge it and ask the next question
11. If user uses Support/Draft/Scrapping commands, provide help but then ask the same question again
12. Do NOT jump to random questions - follow the exact sequence
13. Do NOT list option bullets in your message - the UI displays clickable option buttons

"""
        msgs.append({"role": "system", "content": session_context})
    
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
    
    # Clean up extra newlines (keep "Question X of 46" format for Business Plan)
    reply_content = re.sub(r'\n{3,}', '\n\n', reply_content)  # Clean up 3+ newlines to 2
    
    # Handle remaining commands (kickstart, contact) that weren't processed earlier
    current_phase = session_data.get("current_phase", "") if session_data else ""
    
    if current_phase != "KYC":
        # Only process remaining commands outside of KYC phase
        if user_content.lower() == "kickstart":
            reply_content = handle_kickstart_command(reply_content, history, session_data)
        elif user_content.lower() == "who do i contact?":
            reply_content = handle_contact_command(reply_content, history, session_data)
    
    # Inject missing tag if AI forgot to include one
    reply_content = inject_missing_tag(reply_content, session_data)
    
    # Check if AI response contains WEBSEARCH_QUERY (from scrapping command)
    if "WEBSEARCH_QUERY:" in reply_content:
        needs_web_search = True
        web_search_query = reply_content.split("WEBSEARCH_QUERY:")[1].strip()
        print(f"🔍 Web search triggered by AI response: {web_search_query}")
        # Remove the WEBSEARCH_QUERY from the response
        reply_content = reply_content.split("WEBSEARCH_QUERY:")[0].strip()
    
    # Format response structure to use proper list format instead of paragraph
    reply_content = format_response_structure(reply_content)
    
    # Ensure questions are properly separated
    reply_content = ensure_question_separation(reply_content, session_data)
    
    # Extract question tag from reply and update session data BEFORE sequence validation
    patch_session = {}
    tag_match = re.search(r'\[\[Q:([A-Z_]+\.\d+)\]\]', reply_content)
    if tag_match and session_data:
        new_question_tag = tag_match.group(1)
        current_asked_q = session_data.get("asked_q", "")
        
        # Only update if this is a new question (not the same as current)
        if new_question_tag != current_asked_q:
            # Update session data immediately for sequence validation
            session_data["asked_q"] = new_question_tag
            patch_session["asked_q"] = new_question_tag
            print(f"🔧 Updating session asked_q: {current_asked_q} → {new_question_tag}")
    
    # Validate business plan question sequence (now with updated session data)
    reply_content = validate_business_plan_sequence(reply_content, session_data)
    
    # Fix verification flow to separate verification from next question
    # reply_content = fix_verification_flow(reply_content, session_data)
    
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
    
    # Check if user just answered the final KYC question OR if AI generated a completion message
    if session_data and session_data.get("current_phase") == "KYC":
        current_tag = session_data.get("asked_q", "")
        
        # Check if the AI's reply contains a completion message (fallback detection)
        completion_indicators = [
            "we've completed your entrepreneurial profile",
            "fantastic! we've completed your entrepreneurial",
            "completed your entrepreneurial profile",
            "ready to dive into your business planning",
            "moving into the exciting business planning phase"
        ]
        
        if any(indicator in reply_content.lower() for indicator in completion_indicators):
            print(f"🎯 AI generated completion message detected - triggering proper completion handler")
            return await handle_kyc_completion(session_data, history)
        
        # Original detection: Check if on question 19 and user answered
        if current_tag and current_tag.startswith("KYC."):
            try:
                question_num = int(current_tag.split(".")[1])
                # Check if user just answered the final question (19)
                if (question_num == 19 and 
                    not current_tag.endswith("_ACK") and
                    ("proactive" in user_content.lower() or 
                     user_content.lower().strip() in ["yes", "y", "yeah", "yep", "sure", "ok", "okay", "absolutely", "definitely", "no", "n", "nope", "NO", "NOPE" , "proactive" , "Proactive" , "excellent" , "Excellent" , "fantastic" , "Fantastic" , "congratulations" , "Congratulations"] or
                     "yes" in user_content.lower() or
                     "no" in user_content.lower())):
                    
                    print(f"🎯 User answered final KYC question (19) - triggering completion immediately")
                    # Trigger completion immediately after acknowledgment
                    return await handle_kyc_completion(session_data, history)
            except (ValueError, IndexError):
                pass
    
    
    # Use AI to determine if Accept/Modify buttons should be shown
    button_detection = await should_show_accept_modify_buttons(reply_content, user_content)
    
    return {
        "reply": reply_content,
        "web_search_status": web_search_status,
        "immediate_response": immediate_response,
        "patch_session": patch_session if patch_session else None,
        "show_accept_modify": button_detection.get("show_buttons", False)
    }

async def handle_draft_command(reply, history, session_data=None):
    """Handle the Draft command with comprehensive response generation"""
    # Extract context from conversation history
    context_summary = extract_conversation_context(history)
    business_context = extract_business_context_from_history(history)
    
    # Get current question context for more targeted responses
    current_question = get_current_question_context(history)
    
    # Generate draft content based on conversation history and current question
    draft_content = await generate_draft_content(history, business_context, current_question)
    
    # Create a comprehensive draft response with clear heading
    draft_response = f"Here's a draft for you:\n\n{draft_content}\n\n"
    
    return draft_response

def get_current_question_context(history):
    """Extract the current question context from the most recent assistant message"""
    # Look for the most recent assistant message that contains a question tag
    for msg in reversed(history[-8:]):  # Look at last 8 messages to find the actual question
        if msg.get('role') == 'assistant' and msg.get('content'):
            content = msg['content'].lower()
            # Skip command responses and look for actual questions
            if any(command in content for command in ['here\'s a draft', 'let\'s work through this', 'here\'s a refined version', 'verification:', 'here\'s what i\'ve captured']):
                continue
            # Look for question tags or question indicators
            if '[[' in content and ']]' in content and any(indicator in content for indicator in ['what', 'how', 'when', 'where', 'why', 'do you', 'are you', 'can you']):
                question_text = content
                print(f"🔍 DEBUG - Found current question: {question_text[:200]}...")
                return question_text
    print("🔍 DEBUG - No question found in recent history")
    return ""

def get_question_topic(current_question):
    """Extract the main topic from the current question"""
    if not current_question:
        print("🔍 DEBUG - No current question provided to get_question_topic")
        return "business planning"
    
    if any(keyword in current_question for keyword in ['problem does your business solve', 'who has this problem', 'problem', 'solve', 'pain point', 'need']):
        print("🔍 DEBUG - Detected problem-solution topic")
        return "problem-solution fit"
    elif any(keyword in current_question for keyword in ['competitor', 'competition', 'main competitors', 'strengths and weaknesses', 'competitive advantage', 'unique value proposition', 'what makes your business unique']):
        print("🔍 DEBUG - Detected competitive analysis topic")
        return "competitive analysis"
    elif any(keyword in current_question for keyword in ['target market', 'demographics', 'psychographics', 'behaviors', 'ideal customer']):
        print("🔍 DEBUG - Detected target market topic")
        return "target market definition"
    elif any(keyword in current_question for keyword in ['location', 'space', 'facility', 'equipment', 'infrastructure', 'where will your business be located']):
        print("🔍 DEBUG - Detected operational requirements topic")
        return "operational requirements"
    elif any(keyword in current_question for keyword in ['staff', 'hiring', 'team', 'employee', 'operational needs', 'initial staff']):
        print("🔍 DEBUG - Detected staffing needs topic")
        return "staffing needs"
    elif any(keyword in current_question for keyword in ['supplier', 'vendor', 'partner', 'relationship', 'key partners']):
        print("🔍 DEBUG - Detected supplier relationships topic")
        return "supplier and vendor relationships"
    elif any(keyword in current_question for keyword in ['key features and benefits', 'how does it work', 'main components', 'steps involved', 'value or results', 'product', 'service', 'core offering', 'what will you be offering']):
        print("🔍 DEBUG - Detected core product/service topic")
        return "core product or service"
    elif any(keyword in current_question for keyword in ['mission', 'tagline', 'mission statement', 'business stands for']):
        print("🔍 DEBUG - Detected mission statement topic")
        return "mission statement"
    elif any(keyword in current_question for keyword in ['sales', 'projected sales', 'first year', 'sales projections', 'revenue', 'income']):
        print("🔍 DEBUG - Detected sales projections topic")
        return "sales projections"
    elif any(keyword in current_question for keyword in ['startup costs', 'estimated startup costs', 'one-time expenses', 'initial costs', 'launch costs']):
        print("🔍 DEBUG - Detected startup costs topic")
        return "startup costs"
    elif any(keyword in current_question for keyword in ['financial', 'budget', 'costs', 'expenses', 'funding', 'investment']):
        print("🔍 DEBUG - Detected financial planning topic")
        return "financial planning"
    elif any(keyword in current_question for keyword in ['intellectual property', 'patents', 'trademarks', 'copyrights', 'proprietary technology', 'unique processes', 'formulas', 'legal protections']):
        print("🔍 DEBUG - Detected intellectual property topic")
        return "intellectual property"
    elif any(keyword in current_question for keyword in ['product development timeline', 'working prototype', 'mvp', 'milestones', 'launch', 'validate your concept', 'full development']):
        print("🔍 DEBUG - Detected product development topic")
        return "product development"
    else:
        print("🔍 DEBUG - No specific topic detected, using default business planning")
        return "business planning"

async def generate_draft_content(history, business_context, current_question=""):
    """Generate draft content based on conversation history"""
    # Extract recent messages (both user and assistant) to understand context
    recent_messages = []
    for msg in history[-8:]:  # Look at last 8 messages (4 exchanges)
        if msg.get('content'):
            recent_messages.append(msg['content'])
    
    # Debug logging
    print(f"🔍 DEBUG - Recent messages for draft context: {recent_messages}")
    
    # Generate contextual draft based on what they've been discussing
    if not recent_messages:
        return "Based on our conversation, here's a draft response that captures the key points we've discussed and provides a comprehensive answer to your current question."
    
    # Look for key topics in recent messages (both questions and responses)
    recent_text = " ".join(recent_messages).lower()
    print(f"🔍 DEBUG - Recent text for draft analysis: {recent_text[:200]}...")
    
    # Use the current_question parameter if provided, otherwise extract from history
    if not current_question:
        current_question = get_current_question_context(history)
    
    print(f"🔍 DEBUG - Current question context for draft: {current_question[:100]}...")
    
    # Extract business context
    business_name = business_context.get("business_name", "your business")
    industry = business_context.get("industry", "your industry")
    business_type = business_context.get("business_type", "your business type")
    location = business_context.get("location", "your location")
    
    # Extract previous answers from history for better context
    previous_answers = []
    for msg in history[-10:]:
        if msg.get('role') == 'user' and len(msg.get('content', '')) > 20:
            content = msg.get('content', '')
            # Skip command words
            if content.lower() not in ['support', 'draft', 'scrapping', 'scraping', 'accept', 'modify']:
                previous_answers.append(content[:200])
    
    # Use AI to generate a comprehensive, personalized draft
    draft_prompt = f"""
    Create a comprehensive, detailed draft answer for this business question: "{current_question}"
    
    Business Context:
    - Business Name: {business_name}
    - Industry: {industry}
    - Business Type: {business_type}
    - Location: {location}
    
    Previous Answers and Context:
    {' | '.join(previous_answers[-3:]) if previous_answers else 'No previous context available'}
    
    Generate a complete, well-structured draft answer that:
    1. Directly answers the question with specific, actionable content
    2. Is personalized to {business_name} in the {industry} industry
    3. Considers the {location} market and local factors
    4. Provides concrete details and examples (not generic advice)
    5. Is appropriate for a {business_type} business structure
    6. Uses information from previous answers when relevant
    7. Includes bullet points or numbered lists for clarity
    8. Is comprehensive enough to be used as-is (400-600 words)
    
    Structure the draft with clear sections like:
    - Main answer/core content
    - Key points or features (use bullet points)
    - Specific considerations for the business
    - Next steps or recommendations
    
    Make this a complete, polished draft that the user can accept and use immediately. Be specific and detailed, not generic.
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": draft_prompt}],
            temperature=0.3,
            max_tokens=1500  # Increased for detailed draft responses
        )
        
        ai_draft = response.choices[0].message.content
        print(f"🔍 DEBUG - AI-generated draft length: {len(ai_draft)} characters")
        return ai_draft
    except Exception as e:
        print(f"AI draft generation failed: {e}, falling back to template-based drafts")
        # Fall back to template-based drafts if AI generation fails
        pass
    
    # Check for specific business plan question topics based on current question
    if any(keyword in current_question for keyword in ['problem does your business solve', 'who has this problem', 'problem', 'solve', 'pain point', 'need']):
        return generate_problem_solution_draft(business_context, history)
    
    elif any(keyword in current_question for keyword in ['competitor', 'competition', 'main competitors', 'strengths and weaknesses', 'competitive advantage', 'unique value proposition', 'what makes your business unique']):
        return generate_competitive_analysis_draft(business_context, history)
    
    elif any(keyword in current_question for keyword in ['target market', 'demographics', 'psychographics', 'behaviors', 'ideal customer']):
        return generate_target_market_draft(business_context, history)
    
    elif any(keyword in current_question for keyword in ['location', 'space', 'facility', 'equipment', 'infrastructure', 'where will your business be located']):
        return generate_operational_requirements_draft(business_context, history)
    
    elif any(keyword in current_question for keyword in ['staff', 'hiring', 'team', 'employee', 'operational needs', 'initial staff']):
        return generate_staffing_needs_draft(business_context, history)
    
    elif any(keyword in current_question for keyword in ['supplier', 'vendor', 'partner', 'relationship', 'key partners']):
        return generate_supplier_relationships_draft(business_context, history)
    
        return f"""Based on your business vision, here's a draft for your key features and benefits:

{business_context.get('business_name', 'Your business')} offers advanced AI-powered features that provide significant productivity benefits to customers. The main components include intelligent voice recognition technology, automated text formatting, and seamless integration capabilities.

**Key Features:**
- Advanced AI-powered voice recognition with 95%+ accuracy
- Automated text formatting and organization
- Multiple output formats (plain text, formatted documents, blog posts)
- Real-time processing with instant results
- Cloud-based storage and access
- Integration with popular productivity tools

**Customer Benefits:**
- Dramatic time savings (up to 80% reduction in transcription time)
- Improved accuracy compared to manual transcription
- Enhanced productivity and workflow efficiency
- Cost-effective solution for content creation
- Easy-to-use interface requiring no technical expertise

**How It Works:**
Customers experience seamless results through a simple three-step process: 1) Upload voice recordings via web interface, 2) AI processes and transcribes audio with intelligent formatting, 3) Download formatted text in preferred format. The entire process takes under 5 minutes for most recordings.

**Measurable Results:**
Customers can expect 95%+ transcription accuracy, processing times under 5 minutes, and significant productivity improvements in their content creation workflows."""
    
    elif any(keyword in current_question for keyword in ['intellectual property', 'patents', 'trademarks', 'copyrights', 'proprietary technology', 'unique processes', 'formulas', 'legal protections']):
        return generate_intellectual_property_draft(business_context, history)
    
    elif any(keyword in current_question for keyword in ['product', 'service', 'core offering', 'what will you be offering']):
        business_name = business_context.get("business_name", "Your business")
        industry = business_context.get("industry", "your industry")
        business_type = business_context.get("business_type", "your business type")
        
        return f"""Based on your business vision, here's a draft for your core product or service: 

{business_name} offers innovative solutions in the {industry} sector designed to help customers achieve their goals more efficiently. As a {business_type}, we focus on delivering value through specialized expertise and customer-centric approaches.

**Core Features:**
- Specialized solutions tailored to the {industry} market
- Customer-focused service delivery
- Innovative approaches to common challenges
- Scalable solutions that grow with customer needs

**Key Benefits:**
- Improved efficiency and productivity for customers
- Cost-effective solutions compared to alternatives
- Expert guidance and support
- Customized approaches for different customer segments

**Customer Experience:**
Customers interact with {business_name} through a streamlined process that focuses on understanding their specific needs and delivering tailored solutions. Our approach emphasizes clear communication, quality service, and measurable results.

**Unique Value Proposition:**
{business_name} combines industry expertise with innovative approaches to deliver superior solutions in the {industry} sector. Our focus on customer success and continuous improvement sets us apart from competitors.

**Expected Outcomes:**
Customers can expect improved results, enhanced efficiency, and ongoing support that helps them achieve their business objectives in the {industry} sector."""
    
    elif any(keyword in current_question for keyword in ['mission', 'tagline', 'mission statement', 'business stands for']):
        business_name = business_context.get("business_name", "Your business")
        industry = business_context.get("industry", "your industry")
        
        return f"""Based on your business vision, here's a draft mission statement:

"{business_name} aims to deliver innovative solutions in the {industry} sector, empowering customers to achieve their goals through expert guidance, quality service, and continuous improvement."

**Core Values:**
- Customer-centric approach and service excellence
- Innovation and continuous improvement
- Integrity and transparency in all interactions
- Commitment to delivering measurable results
- Building long-term partnerships with customers

**Purpose Statement:**
We believe that every customer deserves solutions that are tailored to their specific needs and delivered with expertise and care. By focusing on understanding our customers' challenges and goals, we provide value that goes beyond expectations.

**Unique Positioning:**
{business_name} stands for combining industry expertise with personalized service, making professional solutions accessible and effective for customers in the {industry} sector."""
    
    elif any(keyword in current_question for keyword in ['sales', 'projected sales', 'first year', 'sales projections', 'revenue', 'income']):
        return "Based on your business goals, here's a draft for your first-year sales projections: Your projected sales for the first year should be based on realistic market analysis and conservative estimates. Consider factors like your target market size, customer acquisition rate, pricing strategy, and seasonal variations. Focus on creating projections that account for market penetration, customer lifetime value, and repeat business. Think about how you'll reach customers and what conversion rates you can realistically expect based on industry benchmarks and your marketing capabilities."
    
    elif any(keyword in current_question for keyword in ['startup costs', 'estimated startup costs', 'one-time expenses', 'initial costs', 'launch costs']):
        return "Based on your business needs, here's a draft for your startup costs: Your estimated startup costs should include essential one-time expenses like equipment purchases, initial inventory, legal fees, permits and licenses, website development, initial marketing campaigns, and office setup. Consider both essential startup costs and optional investments that could be deferred to manage cash flow. Focus on creating a comprehensive list of all one-time expenses needed to launch your business, including equipment, technology, legal requirements, and initial marketing. Think about equipment leasing vs. buying, bulk purchasing discounts, and phased implementation to optimize your startup investment."
    
    elif any(keyword in current_question for keyword in ['financial', 'budget', 'costs', 'expenses', 'funding', 'investment']):
        return "Based on your business requirements, here's a draft for your financial planning: Your financial plan should include startup costs, operating expenses, cash flow projections, and funding requirements. Consider fixed costs (rent, salaries, equipment) and variable costs (materials, marketing, commissions). Focus on creating realistic budgets, identifying funding sources, and planning for financial sustainability. Think about break-even analysis, profit margins, and financial contingency planning to ensure long-term viability."
    
    elif any(keyword in current_question for keyword in ['intellectual property', 'patents', 'trademarks', 'copyrights', 'proprietary technology', 'unique processes', 'formulas', 'legal protections']):
        return generate_intellectual_property_draft(business_context, history)
    
    elif any(keyword in current_question for keyword in ['product development timeline', 'working prototype', 'mvp', 'milestones', 'launch', 'validate your concept', 'full development']):
        business_name = business_context.get("business_name", "your business")
        industry = business_context.get("industry", "your industry")
        business_type = business_context.get("business_type", "your business type")
        
        return f"""Based on your business goals, here's a draft for your product development timeline:

**Development Phases:**
• Phase 1: Concept validation and market research
• Phase 2: Prototype development and initial testing
• Phase 3: MVP creation and user feedback
• Phase 4: Full product development and launch

**Key Milestones:**
• Complete market research and validation
• Develop working prototype
• Create minimum viable product (MVP)
• Conduct testing and validation
• Prepare for full product launch

**Timeline Considerations:**
• Development phases: 3-6 months per phase
• Testing periods: 2-4 weeks for each iteration
• Validation steps: Continuous throughout development
• Resource requirements: Technical team, testing equipment, market research

**Validation Strategy:**
Focus on validating your concept before full development through market research, prototype testing, and user feedback to ensure market fit and demand."""
    
    # Fallback to analyzing recent text if current question doesn't match
    elif any(keyword in recent_text for keyword in ['problem does your business solve', 'who has this problem', 'problem', 'solve', 'pain point', 'need']):
        return generate_problem_solution_draft(business_context, history)
    
    elif any(keyword in recent_text for keyword in ['competitor', 'competition', 'main competitors', 'strengths and weaknesses', 'competitive advantage', 'unique value proposition', 'what makes your business unique']):
        return generate_competitive_analysis_draft(business_context, history)
    
    elif any(keyword in recent_text for keyword in ['target market', 'demographics', 'psychographics', 'behaviors', 'ideal customer']):
        return generate_target_market_draft(business_context, history)
    
    elif any(keyword in recent_text for keyword in ['location', 'space', 'facility', 'equipment', 'infrastructure', 'where will your business be located']):
        return "Based on your business needs, here's a draft for your operational requirements: Your business location should be strategically chosen to maximize accessibility for your target customers while considering operational efficiency. Key factors include proximity to suppliers, transportation access, zoning requirements, and cost considerations. Your space and equipment needs should align with your business operations, ensuring you have adequate facilities to serve your customers effectively while maintaining operational efficiency. Focus on factors like zoning, transportation access, costs, and scalability."
    
    elif any(keyword in recent_text for keyword in ['staff', 'hiring', 'team', 'employee', 'operational needs', 'initial staff']):
        return "Based on your business goals, here's a draft for your staffing needs: Your short-term operational needs should focus on identifying critical roles required for launch, including key personnel who can drive your core business functions. Consider hiring initial staff who bring essential skills and experience, securing appropriate workspace, and establishing operational processes. Prioritize roles that directly impact customer experience and business operations, ensuring you have the right team in place to execute your business plan effectively. Focus on identifying key positions, required qualifications, and your hiring timeline."
    
    elif any(keyword in recent_text for keyword in ['supplier', 'vendor', 'partner', 'relationship', 'key partners']):
        return "Based on your business requirements, here's a draft for your supplier and vendor relationships: You'll need to identify key suppliers and vendors who can provide essential products, services, or resources for your business operations. Consider building relationships with reliable partners who offer competitive pricing, quality products, and consistent service. Key partners might include suppliers for raw materials, service providers for essential business functions, and strategic partners who can help you reach your target market or enhance your offerings. Focus on reliability, quality, pricing, and long-term partnership potential."
    
    elif any(keyword in recent_text for keyword in ['key features and benefits', 'how does it work', 'main components', 'steps involved', 'value or results']):
        return f"Based on your business vision, here's a draft for your key features and benefits: {business_context.get('business_name', 'Your business')} offers advanced AI-powered features that provide significant productivity benefits to customers. The main components include intelligent voice recognition technology, automated text formatting, and seamless integration capabilities. Customers will experience dramatic time savings and improved accuracy through a process that involves uploading audio files, AI processing, and downloading formatted results. Focus on clearly articulating the technical aspects, user experience, and measurable results customers can expect from using your solution."
    
    elif any(keyword in recent_text for keyword in ['product', 'service', 'core offering', 'what will you be offering']):
        return "Based on your business vision, here's a draft for your core product or service: Your core offering is [product/service description] designed to [key benefits]. Consider what specific features, benefits, or outcomes customers will receive and how customers will interact with or use your product/service. Focus on your unique value proposition and how you'll deliver exceptional customer experience. Think about the key features that differentiate you from competitors and the specific outcomes customers can expect."
    
    elif any(keyword in recent_text for keyword in ['intellectual property', 'patents', 'trademarks', 'copyrights', 'proprietary technology', 'unique processes', 'formulas', 'legal protections']):
        return "Based on your business needs, here's a draft for your intellectual property strategy: Your business may have intellectual property assets including [patents/trademarks/copyrights] that protect your [unique processes/formulas/technology]. Consider what legal protections are important for your business, including patent applications for innovative processes, trademark registration for your brand, and copyright protection for original content. Focus on identifying your proprietary assets, understanding the legal requirements for protection, and developing a strategy to safeguard your competitive advantages."
    
    elif any(keyword in recent_text for keyword in ['product development timeline', 'working prototype', 'mvp', 'milestones', 'launch', 'validate your concept', 'full development']):
        return "Based on your business goals, here's a draft for your product development timeline: Your development timeline should include key milestones such as [prototype development], [MVP creation], [testing and validation], and [full product launch]. Consider what working prototype or MVP you currently have and what milestones you need to reach before launch. Focus on creating a realistic timeline that accounts for development phases, testing periods, and validation steps. Think about how you'll validate your concept before full development and what resources you'll need at each stage."
    
    elif any(keyword in recent_text for keyword in ['mission', 'tagline', 'mission statement', 'business stands for']):
        return "Based on your business vision, here's a draft mission statement: [Business name] aims to [core purpose] by [key approach] to [target outcome]. Consider what your business stands for and how you would describe it in one compelling sentence. Think about your core values, purpose, and what makes you unique. Focus on creating a clear, inspiring statement that guides your business decisions and resonates with your target audience."
    
    elif any(keyword in recent_text for keyword in ['sales', 'projected sales', 'first year', 'sales projections', 'revenue', 'income']):
        return "Based on your business goals, here's a draft for your first-year sales projections: Your projected sales for the first year should be based on realistic market analysis and conservative estimates. Consider factors like your target market size, customer acquisition rate, pricing strategy, and seasonal variations. Focus on creating projections that account for market penetration, customer lifetime value, and repeat business. Think about how you'll reach customers and what conversion rates you can realistically expect based on industry benchmarks and your marketing capabilities."
    
    elif any(keyword in recent_text for keyword in ['startup costs', 'estimated startup costs', 'one-time expenses', 'initial costs', 'launch costs']):
        return "Based on your business needs, here's a draft for your startup costs: Your estimated startup costs should include essential one-time expenses like equipment purchases, initial inventory, legal fees, permits and licenses, website development, initial marketing campaigns, and office setup. Consider both essential startup costs and optional investments that could be deferred to manage cash flow. Focus on creating a comprehensive list of all one-time expenses needed to launch your business, including equipment, technology, legal requirements, and initial marketing. Think about equipment leasing vs. buying, bulk purchasing discounts, and phased implementation to optimize your startup investment."
    
    elif any(keyword in recent_text for keyword in ['financial', 'budget', 'costs', 'expenses', 'funding', 'investment']):
        return "Based on your business requirements, here's a draft for your financial planning: Your financial plan should include startup costs, operating expenses, cash flow projections, and funding requirements. Consider fixed costs (rent, salaries, equipment) and variable costs (materials, marketing, commissions). Focus on creating realistic budgets, identifying funding sources, and planning for financial sustainability. Think about break-even analysis, profit margins, and financial contingency planning to ensure long-term viability."
    
    else:
        return "Based on our conversation, here's a comprehensive draft response that addresses your current question with detailed insights and actionable recommendations tailored to your business context and goals. Consider breaking down complex questions into smaller parts and thinking through each aspect systematically."

async def handle_scrapping_command(reply, notes, history, session_data=None):
    """Handle the Scrapping command with actual web search research"""
    print(f"🔍 DEBUG - Scrapping command called with notes: '{notes}'")
    
    # Extract business context from history for targeted research
    business_context = extract_business_context_from_history(history)
    
    # Get current question context for more targeted responses
    current_question = get_current_question_context(history)
    
    # Generate scrapping content based on conversation history and current question
    if notes and len(notes.strip()) > 3:
        # Use the new refine function to actually refine user's input
        scrapping_content = await refine_user_input(notes, business_context, current_question)
    else:
        # Fallback to generic content if no notes provided
        scrapping_content = await generate_scrapping_content(history, business_context, notes, current_question)
    
    scrapping_response = f"Here's a refined version of your thoughts:\n\n{scrapping_content}\n\n"
    
    # If user provided specific research notes, conduct actual web search
    if notes and len(notes.strip()) > 3:
        print(f"🔍 DEBUG - Conducting web search for: '{notes}'")
        scrapping_response += f"**🔍 Researching: {notes}**\n\n"
        scrapping_response += "I'm conducting web search research to provide you with current, actionable insights. This will help refine your approach with real data and trends.\n\n"
        
        # Add web search trigger for the backend to process
        scrapping_response += f"\n\nWEBSEARCH_QUERY: {notes}"
        
        # Return the scrapping response with web search trigger
        return {
            "reply": scrapping_response,
            "web_search_status": {"is_searching": True, "query": notes, "completed": False},
            "immediate_response": None
        }
    else:
        print(f"🔍 DEBUG - No specific research topic, providing contextual analysis with web search")
        # If no specific research request, provide contextual analysis based on current question
        # Trigger web search for general scrapping as well
        web_search_query = f"{business_context.get('business_name', 'business')} {business_context.get('industry', 'business')} {get_question_topic(current_question)}"
        scrapping_response += f"\n\nWEBSEARCH_QUERY: {web_search_query}"
        
        return {
            "reply": scrapping_response,
            "web_search_status": {"is_searching": True, "query": web_search_query, "completed": False},
            "immediate_response": None
        }
    
    print(f"🔍 DEBUG - Scrapping response generated, length: {len(scrapping_response)}")
    return {
        "reply": scrapping_response,
        "web_search_status": {"is_searching": False, "query": None, "completed": False},
        "immediate_response": None
    }

async def refine_user_input(user_notes, business_context, current_question=""):
    """Refine user's actual input instead of generating generic content"""
    business_name = business_context.get("business_name", "your business")
    industry = business_context.get("industry", "your industry")
    business_type = business_context.get("business_type", "your business type")
    location = business_context.get("location", "your location")
    
    print(f"🔍 DEBUG - Refining user input: '{user_notes}' for {business_name}")
    
    # Clean up the user's notes
    cleaned_notes = user_notes.strip()
    
    # Use AI to refine and expand on user's input with proper context
    refine_prompt = f"""
    Take this user's rough notes/ideas and refine them into a comprehensive, well-structured answer for the question: "{current_question}"
    
    User's Notes/Ideas:
    "{cleaned_notes}"
    
    Business Context:
    - Business Name: {business_name}
    - Industry: {industry}
    - Business Type: {business_type}
    - Location: {location}
    
    Your task:
    1. Take the user's rough ideas and refine them into polished, professional content
    2. Expand on their ideas with industry-specific insights for {industry}
    3. Add relevant details and context appropriate for a {business_type} in {location}
    4. Structure the content clearly with sections and bullet points
    5. Keep the user's core ideas but make them more comprehensive and actionable
    6. Add strategic recommendations that build on their initial thoughts
    7. Make it 300-500 words of refined, detailed content
    
    Structure your refined version with:
    **Refined Core Concept:**
    [Their idea, polished and expanded]
    
    **Industry-Specific Application:**
    [How this applies to the {industry} industry specifically]
    
    **Strategic Recommendations:**
    [3-5 specific recommendations building on their ideas]
    
    **Implementation Steps:**
    [4-6 concrete steps they can take]
    
    **Key Considerations:**
    [2-3 important factors to consider]
    
    Make this a comprehensive refinement that takes their rough ideas and turns them into polished, actionable content.
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": refine_prompt}],
            temperature=0.3,
            max_tokens=1500  # Increased for detailed refinement
        )
        
        refined_content = response.choices[0].message.content
        print(f"🔍 DEBUG - AI-refined content length: {len(refined_content)} characters")
        return refined_content
    except Exception as e:
        print(f"AI refinement failed: {e}, falling back to basic refinement")
        # Fallback to basic refinement if AI fails
        if len(cleaned_notes) < 50:
            return f"""Based on your input "{cleaned_notes}", here's a refined version:

**Core Concept:**
{cleaned_notes}

**Refined Analysis:**
For {business_name} in the {industry} sector, this concept can be developed into a strategic approach that aligns with your {business_type} business model.

**Key Considerations:**
• Strategic alignment with your business goals
• Customer value proposition
• Implementation requirements
• Resource needs

**Next Steps:**
• Define specific implementation details
• Identify potential challenges
• Develop action plan"""
        
        # For longer notes, provide a concise refinement
        return f"""Based on your detailed input, here's a refined version:

**Your Core Idea:**
{cleaned_notes}

**Refined Analysis:**
This concept shows strong potential for {business_name} in the {industry} sector. The approach aligns well with {business_type} business models and can provide significant value to your target market in {location}.

**Strategic Recommendations:**
• Focus on core value proposition
• Identify key implementation steps
• Consider market positioning
• Plan for scalability

**Implementation Focus:**
• Define specific deliverables
• Establish success metrics
• Create timeline for execution"""

async def generate_scrapping_content(history, business_context, notes, current_question=""):
    """Generate concise scrapping content based on conversation history and research notes"""
    # Extract business context
    business_name = business_context.get("business_name", "your business")
    industry = business_context.get("industry", "your industry")
    business_type = business_context.get("business_type", "your business type")
    location = business_context.get("location", "your location")
    
    # Extract previous answers from history for better context
    previous_answers = []
    for msg in history[-10:]:
        if msg.get('role') == 'user' and len(msg.get('content', '')) > 20:
            content = msg.get('content', '')
            # Skip command words
            if content.lower() not in ['support', 'draft', 'scrapping', 'scraping', 'accept', 'modify']:
                previous_answers.append(content[:200])
    
    # Use AI to generate comprehensive scrapping analysis
    scrapping_prompt = f"""
    Generate a comprehensive, refined analysis that helps answer this business question: "{current_question}"
    
    Business Context:
    - Business Name: {business_name}
    - Industry: {industry}
    - Business Type: {business_type}
    - Location: {location}
    
    Previous Context:
    {' | '.join(previous_answers[-3:]) if previous_answers else 'No previous context available'}
    
    Research Notes (if provided):
    {notes if notes else 'No specific research notes provided'}
    
    Create a detailed, refined analysis that:
    1. Synthesizes relevant information from the business context
    2. Provides industry-specific insights for the {industry} sector
    3. Considers market dynamics in {location}
    4. Offers strategic recommendations appropriate for a {business_type}
    5. Includes current industry trends and best practices (2024-2025)
    6. Provides actionable next steps
    7. Is comprehensive and detailed (400-500 words)
    
    Structure your analysis with these sections:
    **Business Context Analysis:**
    [Overview of the business and how it relates to the question]
    
    **Industry-Specific Insights:**
    [3-4 insights specific to the {industry} industry]
    
    **Market Opportunities:**
    [2-3 opportunities in the {location} market]
    
    **Strategic Recommendations:**
    [4-5 specific, actionable recommendations]
    
    **Implementation Priorities:**
    [3-4 priority actions to take]
    
    **Key Success Factors:**
    [2-3 factors critical for success]
    
    Make this comprehensive, strategic, and highly actionable.
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": scrapping_prompt}],
            temperature=0.3,
            max_tokens=1500  # Increased for detailed scrapping analysis
        )
        
        scrapping_content = response.choices[0].message.content
        print(f"🔍 DEBUG - AI-generated scrapping content length: {len(scrapping_content)} characters")
        return scrapping_content
    except Exception as e:
        print(f"AI scrapping generation failed: {e}, falling back to basic analysis")
        # Fallback to basic analysis
        return f"""Based on your business context, here's a refined analysis for {business_name}:

**Business Overview:**
{business_name} operates in the {industry} sector as a {business_type} business located in {location}.

**Key Focus Areas:**
• Market positioning in the {industry} sector
• Customer value proposition development
• Operational efficiency and scalability
• Competitive differentiation strategies

**Strategic Recommendations:**
• Focus on core strengths and unique value propositions
• Develop targeted customer acquisition strategies
• Implement efficient operational processes
• Build sustainable competitive advantages

**Next Steps:**
• Define specific implementation priorities
• Identify key success metrics
• Create actionable development timeline"""

async def handle_support_command(reply, history, session_data=None):
    """Handle the Support command with proactive research assistance"""
    # Extract business context for verification
    business_context = extract_business_context_from_history(history)
    
    # Get current question context for more targeted responses
    current_question = get_current_question_context(history)
    
    # Generate support content based on conversation history and current question
    support_content = await generate_support_content(history, business_context, current_question)
    
    support_response = f"Let's work through this together with some deeper context:\n\n{support_content}\n\n"
    
    return support_response

async def generate_support_content(history, business_context, current_question=""):
    """Generate support content based on conversation history"""
    # Extract recent messages (both user and assistant) to understand context
    recent_messages = []
    for msg in history[-8:]:  # Look at last 8 messages (4 exchanges)
        if msg.get('content'):
            recent_messages.append(msg['content'])
    
    # Debug logging
    print(f"🔍 DEBUG - Recent messages for support context: {recent_messages}")
    
    # Generate contextual support based on what they've been discussing
    if not recent_messages:
        return "I'm here to provide comprehensive support for your business planning journey. Let me help you think through the current question with additional insights and guidance."
    
    # Look for key topics in recent messages (both questions and responses)
    recent_text = " ".join(recent_messages).lower()
    print(f"🔍 DEBUG - Recent text for analysis: {recent_text[:200]}...")
    
    # Use the current_question parameter if provided, otherwise extract from history
    if not current_question:
        current_question = get_current_question_context(history)
    
    print(f"🔍 DEBUG - Current question context: {current_question[:100]}...")
    
    # DYNAMIC APPROACH: Use AI model to generate industry-specific support
    business_name = business_context.get("business_name", "your business")
    industry = business_context.get("industry", "your industry")
    business_type = business_context.get("business_type", "your business type")
    location = business_context.get("location", "your location")
    
    # Extract previous answers from history for better context
    previous_answers = []
    for msg in history[-10:]:
        if msg.get('role') == 'user' and len(msg.get('content', '')) > 20:
            content = msg.get('content', '')
            # Skip command words
            if content.lower() not in ['support', 'draft', 'scrapping', 'scraping', 'accept', 'modify']:
                previous_answers.append(content[:200])
    
    # Generate dynamic support using AI model with enhanced prompt
    support_prompt = f"""
    Generate comprehensive, highly detailed, and industry-specific guidance for this business question: "{current_question}"
    
    Business Context:
    - Business Name: {business_name}
    - Industry: {industry}
    - Business Type: {business_type}
    - Location: {location}
    
    Previous Context from Conversation:
    {' | '.join(previous_answers[-3:]) if previous_answers else 'No previous context available'}
    
    Provide extremely detailed, actionable guidance that:
    1. Is highly specific to the {industry} industry with real examples
    2. Considers the {location} market dynamics and local factors
    3. Is appropriate for a {business_type} with practical implementation steps
    4. Includes 5-7 concrete, actionable steps the entrepreneur can take immediately
    5. References current {industry} industry trends, statistics, and best practices for 2024-2025
    6. Addresses common challenges specific to {industry} businesses in {location}
    7. Provides strategic insights that go beyond basic advice
    
    Structure your response with:
    **Understanding the Question**
    [Detailed explanation of what this question means for their specific business]
    
    **Industry-Specific Insights**
    [3-4 specific insights about the {industry} industry that relate to this question]
    
    **Practical Action Steps**
    [5-7 numbered, detailed action steps they can take]
    
    **Common Challenges & Solutions**
    [2-3 common challenges and how to overcome them]
    
    **Best Practices for {industry} Businesses**
    [3-4 best practices specific to the industry]
    
    Make the guidance extremely comprehensive, detailed, and actionable. Aim for 400-600 words of rich, valuable content.
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": support_prompt}],
            temperature=0.3,
            max_tokens=1500  # Increased from 600 to 1500 for detailed responses
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Dynamic support generation failed: {e}")
        # Fallback to basic guidance
        return f"Let me help you think through this question for your {industry} business. Consider the specific challenges and opportunities in the {industry} sector, especially in {location}. Focus on how this relates to your {business_type} structure and the unique aspects of your industry."
    
    

async def handle_draft_more_command(reply, history, session_data=None):
    """Handle the Draft More command to create additional content"""
    # Extract business context for verification
    business_context = extract_business_context_from_history(history)
    
    # Get current question context for more targeted responses
    current_question = get_current_question_context(history)
    
    # Generate additional content based on current question
    additional_content = await generate_additional_draft_content(history, business_context, current_question)
    
    # Use consistent format with "Here's a draft" to trigger button detection
    draft_more_response = f"Here's a draft for you:\n\n{additional_content}\n\n"
    
    return draft_more_response

async def generate_additional_draft_content(history, business_context, current_question=""):
    """Generate additional draft content based on current question using AI"""
    business_name = business_context.get("business_name", "your business")
    industry = business_context.get("industry", "your industry")
    business_type = business_context.get("business_type", "your business type")
    location = business_context.get("location", "your location")
    
    # Extract previous answers from history for better context
    previous_answers = []
    for msg in history[-10:]:
        if msg.get('role') == 'user' and len(msg.get('content', '')) > 20:
            content = msg.get('content', '')
            # Skip command words
            if content.lower() not in ['support', 'draft', 'scrapping', 'scraping', 'accept', 'modify', 'draft more']:
                previous_answers.append(content[:200])
    
    # Use AI to generate enhanced additional content
    draft_more_prompt = f"""
    The user requested "Draft More" - they want additional, enhanced content on top of what was already provided.
    
    Current Question: "{current_question}"
    
    Business Context:
    - Business Name: {business_name}
    - Industry: {industry}
    - Business Type: {business_type}
    - Location: {location}
    
    Previous Context:
    {' | '.join(previous_answers[-3:]) if previous_answers else 'No previous context available'}
    
    Generate ENHANCED, ADDITIONAL content that:
    1. Takes the original answer to the next level with MORE detail
    2. Adds 3-5 UNIQUE angles or perspectives not typically considered
    3. Provides ADVANCED strategic insights specific to {industry} in {location}
    4. Includes innovative ideas and creative approaches
    5. Offers cutting-edge industry trends and best practices (2024-2025)
    6. Makes it stand out with unique value propositions
    7. Is comprehensive (400-600 words) and highly actionable
    
    Structure your enhanced draft with:
    **Enhanced Main Content:**
    [Take the original concept and elevate it with unique insights]
    
    **Unique Angles & Innovation:**
    [3-5 creative approaches that differentiate from competitors]
    
    **Advanced Strategic Insights:**
    [Deep industry-specific strategies for {industry}]
    
    **Implementation Roadmap:**
    [Detailed 5-7 step plan with specifics]
    
    **Competitive Edge Factors:**
    [What makes this approach uniquely powerful]
    
    Make this draft MORE creative, MORE detailed, and MORE strategic than a standard response. Think outside the box!
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": draft_more_prompt}],
            temperature=0.4,  # Slightly higher for more creativity
            max_tokens=1500
        )
        
        enhanced_content = response.choices[0].message.content
        print(f"🔍 DEBUG - AI-generated enhanced draft length: {len(enhanced_content)} characters")
        return enhanced_content
    except Exception as e:
        print(f"AI enhanced draft generation failed: {e}, falling back to template")
        # Fallback to template if AI fails
        pass
    
    # Fallback templates if AI generation fails
    if any(keyword in current_question.lower() for keyword in ['target market', 'demographics', 'psychographics', 'behaviors', 'ideal customer']):
        return f"""Here's additional detailed content for your target market strategy:

**Customer Journey Mapping:**
Map out the complete customer journey for {business_name} from awareness to purchase to retention. Identify touchpoints where your {business_type} business can engage with customers and create positive experiences that drive loyalty and referrals.

**Market Segmentation Deep Dive:**
Break down your target market into micro-segments within the {industry} sector. Consider factors like company size, decision-making processes, budget ranges, and pain point severity. This helps you create more targeted messaging and offerings.

**Competitive Differentiation:**
Identify specific ways {business_name} can differentiate from competitors in the {industry} space. Focus on unique value propositions, service delivery methods, or customer experience elements that competitors cannot easily replicate.

**Customer Acquisition Channels:**
Detail the specific channels and tactics that work best for reaching your target market in the {industry} sector. Consider both digital and traditional channels, and how they align with your customers' preferences and behaviors.

**Pricing Strategy Alignment:**
Ensure your pricing strategy aligns with your target market's willingness to pay and budget constraints. Consider value-based pricing that reflects the specific benefits your {business_type} solution provides to customers in the {industry} sector."""

    elif any(keyword in current_question.lower() for keyword in ['competitor', 'competition', 'main competitors', 'strengths and weaknesses', 'competitive advantage']):
        return f"""Here's additional detailed content for your competitive analysis:

**Competitive Intelligence Framework:**
Develop a systematic approach to monitor competitors in the {industry} sector. Track their pricing changes, product launches, marketing campaigns, and customer feedback to identify opportunities and threats.

**Market Positioning Analysis:**
Analyze how competitors position themselves in the {industry} market and identify positioning gaps that {business_name} can exploit. Consider emotional positioning, functional positioning, and price positioning strategies.

**Competitive Response Strategy:**
Develop specific strategies for how {business_name} will respond to competitive actions. This includes defensive strategies to protect market share and offensive strategies to gain competitive advantage.

**Partnership Opportunities:**
Identify potential partnership opportunities with complementary businesses in the {industry} sector. Strategic partnerships can help {business_name} compete more effectively against larger competitors.

**Innovation Differentiation:**
Focus on innovation areas where {business_name} can lead the {industry} market. Consider technology adoption, service delivery innovation, or business model innovation that creates sustainable competitive advantages."""

    else:
        return f"""Here's additional detailed content for your business planning:

**Implementation Timeline:**
Create a detailed timeline for implementing your strategies, including key milestones, dependencies, and resource requirements. This helps ensure realistic planning and successful execution.

**Risk Assessment and Mitigation:**
Identify potential risks and challenges for {business_name} in the {industry} sector, and develop specific mitigation strategies for each risk. This includes market risks, operational risks, and competitive risks.

**Success Metrics and KPIs:**
Define specific, measurable success metrics that align with your business objectives. Include both leading indicators (early warning signs) and lagging indicators (outcome measures) to track progress effectively.

**Resource Planning:**
Detail the specific resources {business_name} needs to execute your strategies, including human resources, technology, capital, and partnerships. Ensure resource allocation aligns with your strategic priorities.

**Growth Strategy:**
Develop a comprehensive growth strategy that includes market expansion, product development, and scaling considerations. Focus on sustainable growth that maintains quality and customer satisfaction."""

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

def extract_business_context_from_history(history):
    """Extract business context information from conversation history"""
    business_context = {
        "business_name": "",
        "industry": "",
        "location": "",
        "business_type": "",
        "target_market": "",
        "business_idea": ""
    }
    
    print(f"🔍 DEBUG - Extracting business context from {len(history)} messages")
    
    # Extract from all messages (not just recent ones)
    for i, msg in enumerate(history):
        if msg["role"] == "user":
            content = msg["content"]
            content_lower = content.lower()
            
            print(f"🔍 DEBUG - Message {i}: {content[:100]}...")
            
            # Extract business name - prioritize domain names and longer names over short responses
            # First check for domain-like names (highest priority)
            if "." in content and any(ext in content_lower for ext in [".com", ".net", ".org", ".co"]):
                potential_name = content.strip()
                command_words = ["support", "draft", "scrapping", "scraping", "accept", "modify", "ok", "okay", "yes", "no", "small business", "corporation", "llc", "inc", "sole proprietorship"]
                # Limit business name to reasonable length to prevent long content
                if len(potential_name) > 5 and len(potential_name) < 50 and potential_name.lower() not in command_words:
                    business_context["business_name"] = potential_name
                    print(f"🔍 DEBUG - Found domain business name: {potential_name}")
            
            # Then look for patterns like "my business is", "company name", etc.
            elif not business_context["business_name"] and any(phrase in content_lower for phrase in ["my business is", "company name", "startup name", "business name", "what is your business name"]):
                # Extract the name after these phrases
                for phrase in ["my business is", "company name", "startup name", "business name", "what is your business name"]:
                    if phrase in content_lower:
                        parts = content.split(phrase)
                        if len(parts) > 1:
                            potential_name = parts[1].strip().split()[0]
                            if len(potential_name) > 2:
                                business_context["business_name"] = potential_name
                                print(f"🔍 DEBUG - Found business name: {potential_name}")
                                break
            
            # Finally look for direct business name responses (but prioritize longer, more specific names)
            elif not business_context["business_name"] and len(content.strip()) < 100 and not any(word in content_lower for word in ["yes", "no", "maybe", "i", "my", "the", "a", "an"]) and not any(char.isdigit() for char in content.strip()):
                # If it's a short response that looks like a business name (and doesn't contain numbers)
                potential_name = content.strip()
                # Exclude command words and common responses
                command_words = ["support", "draft", "scrapping", "scraping", "accept", "modify", "ok", "okay", "yes", "no", "small business", "corporation", "llc", "inc", "sole proprietorship", "sure", "financial", "personal savings"]
                # Allow domain names and business names with dots, hyphens, etc.
                if len(potential_name) > 2 and potential_name.lower() not in command_words:
                    # Check if it looks like a business name (contains letters and possibly dots, hyphens)
                    if any(c.isalpha() for c in potential_name) and not potential_name.lower() in ["small business", "corporation", "llc", "inc"]:
                        # Only set if we don't have a better name already, or if this is a longer/more specific name
                        if not business_context["business_name"] or len(potential_name) > len(business_context["business_name"]):
                            business_context["business_name"] = potential_name
                            print(f"🔍 DEBUG - Found direct business name: {potential_name}")
            
            # Extract industry information - Use simple keyword matching
            if not business_context["industry"]:
                # Simple keyword detection for common industries
                common_industries = ["technology", "healthcare", "finance", "retail", "manufacturing", "education", "consulting", "food", "restaurant", "ecommerce", "software", "marketing", "real estate", "construction", "transportation", "entertainment", "media", "agriculture", "energy", "automotive", "ai development", "artificial intelligence", "development", "tech", "software development", "web development", "mobile development", "tea stall", "tea", "beverage", "food service", "hospitality", "cafe", "coffee shop"]
                for industry in common_industries:
                    if industry in content_lower:
                        business_context["industry"] = industry.title()
                        print(f"🔍 DEBUG - Identified industry: {industry}")
                        break
            
            # Extract location information
            if not business_context["location"]:
                # Look for location mentions
                if any(phrase in content_lower for phrase in ["located in", "based in", "karachi", "lahore", "islamabad", "city", "location"]):
                    # Look for city names or location patterns
                    locations = ["karachi", "lahore", "islamabad", "rawalpindi", "faisalabad", "multan", "peshawar", "quetta", "sialkot", "gujranwala"]
                    for location in locations:
                        if location in content_lower:
                            business_context["location"] = location.title()
                            print(f"🔍 DEBUG - Found location: {location}")
                            break
                    # If no specific city found, look for "located in" pattern
                    if not business_context["location"] and "located in" in content_lower:
                        parts = content.split("located in")
                        if len(parts) > 1:
                            potential_location = parts[1].strip().split()[0]
                            if len(potential_location) > 2:
                                business_context["location"] = potential_location.title()
                                print(f"🔍 DEBUG - Found location from pattern: {potential_location}")
            
            # Extract business type
            if not business_context["business_type"]:
                # Look for business type mentions
                if any(phrase in content_lower for phrase in ["business type", "type of business", "startup", "company", "corporation", "llc", "partnership"]):
                    business_types = ["startup", "company", "corporation", "llc", "partnership", "sole proprietorship", "nonprofit", "franchise"]
                    for biz_type in business_types:
                        if biz_type in content_lower:
                            business_context["business_type"] = biz_type
                            print(f"🔍 DEBUG - Found business type: {biz_type}")
                            break
            
            # Extract business idea - look for longer descriptive responses
            if not business_context["business_idea"] and len(content.strip()) > 20:
                # Look for business idea descriptions with specific keywords
                if any(phrase in content_lower for phrase in ["tea good", "on tap", "business idea", "my idea", "startup idea", "venture", "business concept"]):
                    # For tea-related descriptions, capture the full content
                    if any(phrase in content_lower for phrase in ["tea good", "on tap"]):
                        business_context["business_idea"] = content.strip()
                        print(f"🔍 DEBUG - Found tea business idea: {content}")
                    else:
                        # Extract a reasonable portion of the business idea
                        for phrase in ["business idea", "my idea", "startup idea", "venture", "business concept"]:
                            if phrase in content_lower:
                                parts = content.split(phrase)
                                if len(parts) > 1:
                                    idea_text = parts[1].strip()[:100]  # First 100 characters
                                    if len(idea_text) > 10:
                                        business_context["business_idea"] = idea_text
                                        print(f"🔍 DEBUG - Found business idea: {idea_text}")
                                        break
                # Also capture longer responses that might be business ideas (but exclude preference responses)
                elif len(content.strip()) > 30 and not any(word in content_lower for word in ["yes", "no", "maybe", "support", "draft", "scrapping", "hands-on", "decide", "personal savings", "subscriptions", "online only"]):
                    business_context["business_idea"] = content.strip()
                    print(f"🔍 DEBUG - Found business idea (long response): {content[:50]}...")
    
    print(f"🔍 DEBUG - Final business context: {business_context}")
    return business_context

async def handle_competitor_research_request(user_input, business_context, history):
    """Handle specific requests for competitor research"""
    
    # Extract business information for targeted research
    industry = business_context.get("industry", "")
    location = business_context.get("location", "")
    business_name = business_context.get("business_name", "")
    business_type = business_context.get("business_type", "")
    
    # Create targeted research queries
    research_queries = []
    
    if industry:
        research_queries.append(f"main competitors in {industry} industry")
        research_queries.append(f"top companies in {industry} market")
        research_queries.append(f"{industry} industry leaders and market share")
    
    if location and industry:
        research_queries.append(f"{industry} companies in {location}")
        research_queries.append(f"local {industry} competitors in {location}")
    
    if business_type:
        research_queries.append(f"{business_type} business competitors")
        research_queries.append(f"successful {business_type} companies")
    
    # Conduct web search for competitor research
    competitor_research_results = []
    
    for query in research_queries[:3]:  # Limit to 3 queries for efficiency
        try:
            search_result = await conduct_web_search(query)
            if search_result and "unable to conduct web research" not in search_result:
                competitor_research_results.append({
                    "query": query,
                    "result": search_result
                })
        except Exception as e:
            print(f"Error conducting competitor research for query '{query}': {e}")
    
    # Generate comprehensive competitor analysis
    if competitor_research_results:
        analysis_prompt = f"""
        Based on the following research results, provide a comprehensive competitor analysis for a business in the {industry} industry:
        
        Business Context:
        - Industry: {industry}
        - Location: {location}
        - Business Type: {business_type}
        - Business Name: {business_name}
        
        Research Results:
        {chr(10).join([f"Query: {r['query']}{chr(10)}Result: {r['result']}{chr(10)}" for r in competitor_research_results])}
        
        Please provide:
        1. Main competitors identified
        2. Market positioning analysis
        3. Competitive advantages and weaknesses
        4. Market opportunities
        5. Strategic recommendations
        
        Make this analysis actionable and specific to the business context.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.7,
                max_tokens=1500
            )
            
            return {
                "success": True,
                "analysis": response.choices[0].message.content,
                "research_sources": len(competitor_research_results),
                "queries_used": [r["query"] for r in competitor_research_results]
            }
        except Exception as e:
            print(f"Error generating competitor analysis: {e}")
            return {
                "success": False,
                "error": "Failed to generate competitor analysis",
                "research_sources": len(competitor_research_results)
            }
    else:
        return {
            "success": False,
            "error": "Unable to conduct competitor research at this time",
            "research_sources": 0
        }

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

async def handle_roadmap_generation(session_data, history):
    """Handle the transition from Plan to Roadmap phase"""
    
    # Generate comprehensive roadmap using RAG principles
    roadmap_content = await generate_detailed_roadmap(session_data, history)
    
    # Create the roadmap presentation message
    roadmap_message = f"""🗺️ **Your Launch Roadmap is Ready!** 🗺️

Congratulations! Based on your comprehensive business plan, I've generated a detailed, actionable launch roadmap that will guide you from planning to execution.

**"The way to get started is to quit talking and begin doing."** – Walt Disney

---

## 📋 **Your Launch Roadmap Overview**

{roadmap_content}

---

## 🎯 **Key Features of Your Roadmap**

✅ **Research-Backed**: Every recommendation is based on current best practices and industry standards
✅ **Actionable Tasks**: Each phase contains specific, executable tasks with clear timelines
✅ **Multiple Options**: Decision points include various options to fit your specific needs
✅ **Local Resources**: Provider recommendations include local service providers where applicable
✅ **Progress Tracking**: Built-in milestones and success metrics for each phase

---

## 🚀 **What's Next**

Your roadmap is now ready for implementation! Each phase is designed to build upon the previous one, ensuring a smooth transition from planning to execution.

**Ready to begin implementation?** Let me know when you're ready to start executing your roadmap, and I'll guide you through each step with detailed instructions, resources, and support.

---

*This roadmap is tailored specifically to your business, industry, and location. Every recommendation is designed to help you build the business of your dreams.*
"""
    
    return {
        "reply": roadmap_message,
        "transition_phase": "ROADMAP_GENERATED",
        "roadmap_content": roadmap_content
    }

async def handle_roadmap_to_implementation_transition(session_data, history):
    """Handle the transition from Roadmap to Implementation phase"""
    
    # Extract business context from session data
    business_name = session_data.get('business_name', 'Your Business')
    industry = session_data.get('industry', 'general business')
    location = session_data.get('location', 'United States')
    
    # Create comprehensive transition message
    transition_message = f"""🚀 **Roadmap to Implementation Transition** 🚀

Congratulations! You've successfully completed your comprehensive business plan and detailed launch roadmap for "{business_name}". Now it's time to transition from planning into execution mode.

**"Success is not final; failure is not fatal: it is the courage to continue that counts."** – Winston Churchill

---

## 🎯 **Time to Transition from Planning to Action**

You've built a solid foundation with your business plan and roadmap. The time has come to transition from planning into execution mode. This is where your entrepreneurial journey truly begins to take shape.

## 🚀 **What's Next: Implementation Phase**

The Implementation phase will guide you through executing each task step-by-step, turning your roadmap into actionable results. Here's what you can expect:

### **Individual Task Guidance**
- Each task presented with detailed descriptions and clear purposes
- Multiple decision options for informed decision-making
- Mentor insights with research-backed guidance tailored to each step

### **Flexible Navigation & Support**
- Tasks presented one at a time with ability to revisit via navigation menu
- Interactive commands: "Help", "Kickstart", and "Who do I contact?"
- Dynamic prompts and inline notifications for real-time feedback

### **Angel's Implementation Assistance**
Throughout implementation, I can help you with:
- Reviewing and drafting contracts and legal documents
- Completing NDAs and other business documentation
- Analysis and research for business decisions
- Creating pitch decks and presentation materials
- Connecting you with local service providers

### **Service Provider Integration**
- Provider tables with credible local service providers for each step
- Local providers clearly marked for your convenience
- Complete with descriptive information and key considerations

### **Progress Tracking**
- Visual progress bars for overall and per-task completion
- Real-time feedback and suggestions as you complete each task
- Completion declaration reminders with documentation uploads

---

## ⚠️ **Important Implementation Notes**

✅ **Research-Backed**: Every recommendation is grounded in deep research and designed to build your dream business
✅ **Real-Time Support**: You'll receive immediate feedback and suggestions as you complete each task
✅ **Documentation**: Remember to declare task completions and upload relevant documentation
✅ **Progress Tracking**: Progress bars will track your completion throughout the implementation phase

---

## 🎉 **Ready to Begin Implementation?**

Your roadmap is complete and ready for execution. The implementation phase will transform your plans into tangible results, guiding you through each step with expert support and local resources.

**Let's start building your business!** When you're ready, I'll guide you through the first implementation task with detailed instructions, multiple options, and all the support you need to succeed.

*This implementation process is tailored specifically to your "{business_name}" business in the {industry} industry, located in {location}. Every recommendation is designed to help you build the business of your dreams.*
"""
    
    return {
        "reply": transition_message,
        "transition_phase": "ROADMAP_TO_IMPLEMENTATION_TRANSITION",
        "roadmap_content": "Ready for implementation transition"
    }

async def generate_detailed_roadmap(session_data, history):
    """Generate detailed roadmap with RAG-powered research"""
    
    # Extract business context from session data and history
    business_name = session_data.get('business_name', 'Your Business')
    industry = session_data.get('industry', 'general business')
    location = session_data.get('location', 'United States')
    business_type = session_data.get('business_type', 'startup')
    
    # Create comprehensive roadmap prompt with RAG research
    roadmap_prompt = f"""
    Generate a comprehensive, research-backed launch roadmap for "{business_name}" - a {business_type} in the {industry} industry located in {location}.
    
    Use the following business context from the completed business plan:
    - Business Name: {business_name}
    - Industry: {industry}
    - Location: {location}
    - Business Type: {business_type}
    
    Create a detailed roadmap with the following phases. IMPORTANT: Format the response as plain text without any markdown formatting, asterisks, or special characters. Use simple headings and bullet points.
    
    Phase 1: Legal Formation & Compliance
    - Business structure selection (LLC, Corporation, Partnership, etc.)
    - Business registration and licensing requirements
    - Tax ID (EIN) application
    - Required permits and licenses
    - Insurance requirements
    - Compliance with local, state, and federal regulations
    
    Phase 2: Financial Planning & Setup
    - Business bank account setup
    - Accounting system implementation
    - Budget planning and cash flow management
    - Funding strategy execution
    - Financial tracking and reporting systems
    - Tax planning and preparation
    
    Phase 3: Product & Operations Development
    - Supply chain setup and vendor relationships
    - Equipment and technology procurement
    - Operational processes and workflows
    - Quality control systems
    - Inventory management
    - Production or service delivery setup
    
    Phase 4: Marketing & Sales Strategy
    - Brand development and positioning
    - Marketing strategy implementation
    - Sales process setup
    - Customer acquisition channels
    - Digital presence (website, social media)
    - Customer relationship management
    
    Phase 5: Full Launch & Scaling
    - Go-to-market strategy execution
    - Team building and hiring
    - Performance monitoring and analytics
    - Growth and scaling strategies
    - Customer feedback and iteration
    - Long-term sustainability planning
    
    For each phase, provide:
    - Specific Tasks: Detailed, actionable steps
    - Timeline: Realistic time estimates
    - Resources Needed: Required tools, services, and expertise
    - Success Metrics: How to measure progress
    - Decision Points: Multiple options where applicable
    - Local Resources: Service providers and resources specific to {location}
    - Potential Challenges: Common obstacles and solutions
    
    Make the roadmap practical, detailed, and tailored to the specific business context. Include specific examples and actionable recommendations.
    
    Format the response as clean, readable text without any markdown syntax, asterisks, or special formatting characters.
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": roadmap_prompt}],
            temperature=0.6,
            max_tokens=3000
        )
        
        # Clean any remaining markdown formatting from the response
        roadmap_content = response.choices[0].message.content
        
        # Remove markdown formatting
        import re
        # Remove headers (## **text**)
        roadmap_content = re.sub(r'#{1,6}\s*\*+([^*]+)\*+', r'\1', roadmap_content)
        # Remove bold formatting (**text**)
        roadmap_content = re.sub(r'\*+([^*]+)\*+', r'\1', roadmap_content)
        # Remove horizontal rules (---)
        roadmap_content = re.sub(r'^[-=]{3,}$', '', roadmap_content, flags=re.MULTILINE)
        # Clean up extra whitespace
        roadmap_content = re.sub(r'\n{3,}', '\n\n', roadmap_content)
        
        return roadmap_content.strip()
    except Exception as e:
        print(f"Error generating detailed roadmap: {e}")
        return "Roadmap generation in progress..."

async def generate_next_question(question_tag: str, session_data: dict) -> str:
    """Generate the next business planning question based on the question tag"""
    
    # Business planning questions mapping
    business_plan_questions = {
        "BUSINESS_PLAN.01": "What problem does your business solve?",
        "BUSINESS_PLAN.02": "Who has this problem (your target market)?",
        "BUSINESS_PLAN.03": "What is your solution (product or service)?",
        "BUSINESS_PLAN.04": "How is your solution different from existing alternatives?",
        "BUSINESS_PLAN.05": "What are your key features and benefits?",
        "BUSINESS_PLAN.06": "What is your business model (how will you make money)?",
        "BUSINESS_PLAN.07": "Who are your main competitors?",
        "BUSINESS_PLAN.08": "What is your competitive advantage?",
        "BUSINESS_PLAN.09": "What is your target market size?",
        "BUSINESS_PLAN.10": "How will you reach your customers (marketing strategy)?",
        "BUSINESS_PLAN.11": "What is your pricing strategy?",
        "BUSINESS_PLAN.12": "What are your estimated startup costs?",
        "BUSINESS_PLAN.13": "What are your projected sales for the first year?",
        "BUSINESS_PLAN.14": "What funding do you need and how will you get it?",
        "BUSINESS_PLAN.15": "What are your key operational requirements?",
        "BUSINESS_PLAN.16": "What equipment or technology do you need?",
        "BUSINESS_PLAN.17": "Where will your business be located?",
        "BUSINESS_PLAN.18": "What staff do you need initially?",
        "BUSINESS_PLAN.19": "Who are your key suppliers and vendors?",
        "BUSINESS_PLAN.20": "What legal requirements do you need to meet?",
        "BUSINESS_PLAN.21": "Do you have any intellectual property or proprietary technology?",
        "BUSINESS_PLAN.22": "What is your mission statement or tagline?",
        "BUSINESS_PLAN.23": "What are your short-term goals (first 6 months)?",
        "BUSINESS_PLAN.24": "What are your long-term goals (1-3 years)?",
        "BUSINESS_PLAN.25": "What are the main risks and challenges you face?",
        "BUSINESS_PLAN.26": "How will you measure success?",
        "BUSINESS_PLAN.27": "What is your exit strategy (if applicable)?",
        "BUSINESS_PLAN.28": "What support do you need to launch your business?"
    }
    
    # Get the question text
    question_text = business_plan_questions.get(question_tag, "Please provide additional information about your business.")
    
    # Add the question tag
    formatted_question = f"[[Q:{question_tag}]] {question_text}"
    
    # Add some context and encouragement
    context = f"Great! I'm glad we're making progress.\n\nLet's continue by exploring another important aspect of your business.\n\n{question_text}\n\nConsider: What specific details would help clarify this aspect of your business?\nThink about: How does this relate to your overall business strategy?"
    
    return f"[[Q:{question_tag}]] {context}"

def generate_problem_solution_draft(business_context, history):
    """Generate a specific problem-solution draft based on business context"""
    business_name = business_context.get("business_name", "your business")
    industry = business_context.get("industry", "your industry")
    business_type = business_context.get("business_type", "your business type")
    location = business_context.get("location", "your location")
    
    # Generate contextual content based on actual business context
    return f"""Based on your business vision, here's a draft for your problem-solution fit:

**Problem Identification:**
{business_name} addresses critical challenges in the {industry} sector that affect businesses and individuals in {location}. These challenges include inefficiencies in current processes, lack of specialized expertise, and outdated approaches that limit growth potential.

**Target Audience:**
Your target audience consists of {business_type} businesses and professionals in the {industry} sector who are experiencing these operational challenges and seeking more effective solutions.

**Solution Approach:**
{business_name} provides innovative, specialized solutions that directly address these pain points through:
• Industry-specific expertise and knowledge
• Streamlined processes and methodologies
• Customized approaches for different client needs
• Ongoing support and guidance

**Key Benefits:**
• Improved efficiency and productivity
• Cost-effective solutions compared to alternatives
• Expert guidance and support
• Customized approaches for different segments

**Competitive Advantage:**
Your solution is uniquely positioned because it combines deep industry knowledge with innovative approaches, providing superior value that competitors cannot easily replicate."""

def generate_competitive_analysis_draft(business_context, history):
    """Generate a specific competitive analysis draft based on business context"""
    business_name = business_context.get("business_name", "your business")
    industry = business_context.get("industry", "your industry")
    business_type = business_context.get("business_type", "your business type")
    
    return f"Based on your business context, here's a draft analysis of your competitive landscape: In the {industry} sector, your main competitors likely include established players who offer similar {business_type} solutions. These competitors typically have strengths in brand recognition, resources, and market share, but often have weaknesses in pricing flexibility, customer service personalization, and innovation gaps. {business_name}'s competitive advantage should focus on what makes your solution unique - whether it's better pricing, superior customer experience, innovative features, or specialized expertise in the {industry} sector. Focus on identifying 3-5 key competitors in the {industry} space and analyzing their market positioning, pricing models, and customer base to understand how you can differentiate effectively."

def generate_intellectual_property_draft(business_context, history):
    """Generate a specific intellectual property draft based on business context"""
    business_name = business_context.get("business_name", "your business")
    industry = business_context.get("industry", "your industry")
    business_type = business_context.get("business_type", "your business type")
    
    return f"Based on your business needs, here's a draft for your intellectual property strategy: {business_name} may have intellectual property assets including patents for innovative {business_type} processes, trademarks for your brand identity, and copyrights for original content in the {industry} sector. Consider what legal protections are important for your business, including patent applications for innovative processes or technologies, trademark registration for your brand name and logo, and copyright protection for original content, software, or creative materials. Focus on identifying your proprietary assets, understanding the legal requirements for protection in the {industry} sector, and developing a strategy to safeguard your competitive advantages through appropriate IP protection."

def generate_target_market_draft(business_context, history):
    """Generate a specific target market draft based on business context"""
    business_name = business_context.get("business_name", "your business")
    industry = business_context.get("industry", "your industry")
    business_type = business_context.get("business_type", "your business type")
    location = business_context.get("location", "your location")
    
    return f"""Based on your business goals, here's a draft for your target market:

**Primary Target Audience:**
{business_name}'s ideal customers are {business_type} businesses and professionals in the {industry} sector who are seeking specialized solutions and expertise. These customers value quality service, innovation, and results-driven approaches.

**Demographic Profile:**
• Business Type: {business_type} companies
• Industry Focus: {industry} sector
• Geographic Location: {location} and surrounding areas
• Company Size: Small to medium businesses seeking growth

**Psychographic Characteristics:**
• Value quality service and expertise
• Seek innovative solutions to industry challenges
• Prefer working with specialized service providers
• Focus on efficiency and measurable results

**Customer Behaviors:**
• Research extensively before making decisions
• Prefer direct communication and personalized service
• Value long-term partnerships over transactional relationships
• Respond well to industry-specific expertise and knowledge

**Pain Points:**
• Lack of specialized expertise in the {industry} sector
• Inefficient processes and outdated approaches
• Limited access to innovative solutions
• Need for ongoing support and guidance

**How to Reach Them:**
Focus on industry-specific channels, professional networks, and direct outreach that demonstrates your expertise in the {industry} sector."""

def generate_operational_requirements_draft(business_context, history):
    """Generate a specific operational requirements draft based on business context"""
    business_name = business_context.get("business_name", "your business")
    industry = business_context.get("industry", "your industry")
    business_type = business_context.get("business_type", "your business type")
    location = business_context.get("location", "your location")
    
    return f"Based on your business needs, here's a draft for your operational requirements: {business_name}'s location in {location} should be strategically chosen to maximize accessibility for your target customers while considering operational efficiency for your {business_type} operations. Key factors include proximity to suppliers, transportation access, zoning requirements for {industry} businesses, and cost considerations. Your space and equipment needs should align with your {business_type} operations, ensuring you have adequate facilities to serve your customers effectively while maintaining operational efficiency. Focus on factors like zoning compliance for {industry} businesses, transportation access for customers and suppliers, costs, and scalability as your business grows."

def generate_staffing_needs_draft(business_context, history):
    """Generate a specific staffing needs draft based on business context"""
    business_name = business_context.get("business_name", "your business")
    industry = business_context.get("industry", "your industry")
    business_type = business_context.get("business_type", "your business type")
    
    return f"Based on your business goals, here's a draft for your staffing needs: {business_name}'s short-term operational needs should focus on identifying critical roles required for launch in the {industry} sector, including key personnel who can drive your core {business_type} business functions. Consider hiring initial staff who bring essential skills and experience in {industry}, securing appropriate workspace for your team, and establishing operational processes that support your business model. Prioritize roles that directly impact customer experience and business operations, ensuring you have the right team in place to execute your business plan effectively. Focus on identifying key positions specific to {business_type} operations, required qualifications for {industry} professionals, and your hiring timeline for building a strong foundation team."

def generate_supplier_relationships_draft(business_context, history):
    """Generate a specific supplier relationships draft based on business context"""
    business_name = business_context.get("business_name", "your business")
    industry = business_context.get("industry", "your industry")
    business_type = business_context.get("business_type", "your business type")
    
    return f"Based on your business requirements, here's a comprehensive draft for your supplier and vendor relationships: {business_name} will need to identify key suppliers and vendors who can provide essential products, services, or resources for your {business_type} operations in the {industry} sector. Consider building relationships with reliable partners who offer competitive pricing, quality products, and consistent service. Key partners might include suppliers for raw materials or components specific to {industry}, service providers for essential business functions, and strategic partners who can help you reach your target market or enhance your offerings. Focus on reliability, quality, pricing, and long-term partnership potential. Evaluate potential partners based on their track record in the {industry} sector, financial stability, capacity to meet your needs, and alignment with your business values. Consider backup suppliers to ensure business continuity and negotiate favorable terms that support your growth objectives in the {industry} market."