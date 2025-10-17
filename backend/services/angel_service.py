from openai import AsyncOpenAI
import os
import json
import re
from datetime import datetime
from utils.constant import ANGEL_SYSTEM_PROMPT

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# p
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
        "Here's a draft",
        "Here's a research-backed draft",
        "Here's a draft based on",
        "Let's work through this together",
        "Here's a refined version",
        "I'll create additional content"
    ]
    return any(indicator in response_text for indicator in draft_indicators)

def is_moving_to_next_question(response_text: str) -> bool:
    """Check if response is transitioning to next question (should NOT show buttons)"""
    response_lower = response_text.lower()
    
    # FIRST: Check if this is a Draft/Support/Scrapping response
    # These should NEVER be considered as "moving to next question"
    draft_or_support_indicators = [
        "here's a draft",
        "here's a research-backed draft",
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

async def should_show_accept_modify_buttons(ai_response: str, user_last_input: str = "", session_data: dict = None) -> dict:
    """Determine if Accept/Modify buttons should be shown"""
    user_input_lower = user_last_input.lower().strip()
    
    # Check if user explicitly requested Draft, Support, or Scrapping
    command_keywords = ["draft", "support", "scrapping", "scraping", "draft more"]
    is_command_request = user_input_lower in command_keywords
    
    # Check if response is a draft/support response
    is_draft_response = is_draft_or_support_response(ai_response)
    
    # Check if response is moving to next question
    is_next_question = is_moving_to_next_question(ai_response)
    
    # NEW: Check if user provided an answer in Business Planning phase
    is_business_plan = session_data and session_data.get("current_phase") == "BUSINESS_PLAN"
    is_user_answer = is_business_plan and not user_input_lower in ["accept", "modify", "ok", "okay", "yes", "no"] + command_keywords
    
    # Check if AI is acknowledging/capturing the answer (common patterns)
    acknowledgment_patterns = [
        "thank you",
        "thanks for",
        "great",
        "perfect",
        "excellent",
        "wonderful",
        "i've captured",
        "i've noted",
        "got it",
        "understood",
        "that's helpful",
        "appreciate",
        "makes sense"
    ]
    has_acknowledgment = any(pattern in ai_response.lower()[:200] for pattern in acknowledgment_patterns)
    
    # Check if AI is asking a new question (has [[Q: tag)
    has_question_tag = re.search(r'\[\[Q:[A-Z_]+\.\d+\]\]', ai_response) is not None
    
    # Check if AI explicitly requested Accept/Modify buttons
    has_accept_modify_tag = "[[ACCEPT_MODIFY_BUTTONS]]" in ai_response
    
    # Show buttons if:
        # 1. It's a command response (Draft/Support/Scrapping), OR
    # 2. User provided an answer in Business Plan AND AI acknowledged it AND hasn't moved to next question yet, OR
    # 3. It's a phase completion/transition (KYC completion, Business Plan completion, etc.)
    should_show = False
    
    # Check if this is a phase completion/transition
    is_phase_completion = (
        "congratulations" in ai_response.lower() and 
        ("completed" in ai_response.lower() or "completion" in ai_response.lower()) and
        ("phase" in ai_response.lower() or "profile" in ai_response.lower() or "plan" in ai_response.lower())
    )
    
    if has_accept_modify_tag:
        # AI explicitly requested Accept/Modify buttons (section summary, etc.)
        should_show = True
        reason = "AI requested Accept/Modify buttons"
    elif is_command_request or is_draft_response:
        # Only show buttons for Draft commands, not Support or Scrapping
        if user_input_lower == "draft":
            should_show = not is_next_question
            reason = "Draft command response"
        else:
            # Support and Scrapping commands should not show Accept/Modify buttons
            should_show = False
            reason = f"{user_input_lower.title()} command - guidance provided"
    elif is_phase_completion:
        # Show buttons for phase completions/transitions
        should_show = True
        reason = "Phase completion/transition"
    elif is_user_answer and has_acknowledgment and not has_question_tag:
        # Show when AI acknowledges answer but hasn't asked next question yet
        should_show = True
        reason = "Answer acknowledged in Business Plan"
    elif is_user_answer and len(user_last_input.strip()) > 10 and "[[Q:" in ai_response:
        # If AI immediately asks next question after answer, DON'T show buttons
        # (AI is moving forward - user already provided good answer)
        should_show = False
        reason = "Moving to next question immediately"
    else:
        reason = "Standard response"
    
    print(f"🔍 Button Detection:")
    print(f"  - User input: '{user_last_input[:50]}...'")
    print(f"  - Is command request: {is_command_request}")
    print(f"  - Is draft response: {is_draft_response}")
    print(f"  - Is next question: {is_next_question}")
    print(f"  - Is user answer (BP): {is_user_answer}")
    print(f"  - Has acknowledgment: {has_acknowledgment}")
    print(f"  - Has question tag: {has_question_tag}")
    print(f"  - Has accept/modify tag: {has_accept_modify_tag}")
    print(f"  - Is phase completion: {is_phase_completion}")
    print(f"  - Reason: {reason}")
    print(f"  - Should show buttons: {should_show}")
    
    return {
        "show_buttons": should_show,
        "content_length": len(ai_response)
    }

async def conduct_web_search(query):
    """Conduct aggressive web search with citations from authoritative sources"""
    try:
        print(f"🔍 Conducting comprehensive web search: {query}")
        
        # Limit query length reasonably
        if len(query) > 150:
            query = query[:150] + "..."
        
        # Enhanced search prompt with source citations
        search_prompt = f"""Search reputable websites including industry publications, government websites (.gov), 
academic sources (.edu), and authoritative business references for information about: {query}

Provide a comprehensive answer with:
    1. Key findings and data points
2. Current trends and statistics (2024-2025 where available)
3. Cite specific sources with URLs when possible
4. Include quantitative data when available

Format your response with clear sections and citations."""
        
        response = await client.chat.completions.create(
            model="gpt-4o",  # Use full model for better research
            messages=[{
                "role": "user", 
                "content": search_prompt
            }],
            temperature=0.2,  # Lower temperature for factual accuracy
            max_tokens=800,  # Increased for comprehensive research
            timeout=10.0  # Longer timeout for thorough research
        )
        
        # Extract search results from response
        search_results = response.choices[0].message.content
        print(f"✅ Web search completed for: {query[:50]}... (length: {len(search_results)} chars)")
        return search_results
    
    except Exception as e:
        print(f"❌ Web search error: {e}")
        return None

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
                
                # Same question number is VALID because session updates before validation
                # This happens when: user answers Q35 → session updates to Q36 → AI generates Q36
                # The validation sees Q36 == Q36, which is correct!
                elif current_q_num == last_q_num:
                    print(f"✅ Correct question sequence: {current_q_num} (session already updated)")
                    # DO NOT force progression - this is correct behavior!

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
    """Check if we need to provide a section summary based on the current question tag
    
    TIMING: This checks if user just ANSWERED a section-ending question.
    It should trigger AFTER user answers Q4, Q8, Q12, Q17, Q25, Q31, Q37, Q41, or Q45.
    """
    
    if not current_tag or not current_tag.startswith("BUSINESS_PLAN."):
        return None
    
    try:
        question_num = int(current_tag.split(".")[1])
    except (ValueError, IndexError):
        return None
    
    # Define section boundaries - these are the LAST questions in each section
    # When user answers these questions, we show a section summary BEFORE moving to next section
    section_boundaries = {
        4: "SECTION 1 SUMMARY REQUIRED: After BUSINESS_PLAN.04, provide:",
        8: "SECTION 2 SUMMARY REQUIRED: After BUSINESS_PLAN.08, provide:",
        12: "SECTION 3 SUMMARY REQUIRED: After BUSINESS_PLAN.12, provide:",
        17: "SECTION 4 SUMMARY REQUIRED: After BUSINESS_PLAN.17, provide:",
        25: "SECTION 5 SUMMARY REQUIRED: After BUSINESS_PLAN.25, provide:",
        31: "SECTION 6 SUMMARY REQUIRED: After BUSINESS_PLAN.31, provide:",
        37: "SECTION 7 SUMMARY REQUIRED: After BUSINESS_PLAN.37, provide:",
        41: "SECTION 8 SUMMARY REQUIRED: After BUSINESS_PLAN.41, provide:",
        45: "SECTION 9 SUMMARY REQUIRED: After BUSINESS_PLAN.45, provide:"
    }
    
    # Check if we're at a section boundary
    if question_num in section_boundaries:
        print(f"✅ SECTION SUMMARY TRIGGERED: User just answered Q{question_num}, showing {get_section_name(question_num)} section summary")
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
        37: "Legal & Compliance",
        41: "Growth & Scaling",
        45: "Risk Management"
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
    """
    Handle the transition from KYC completion to Business Planning Exercise
    This is the missing transition that introduces the Business Planning phase
    """
    
    # Generate KYC summary insights
    kyc_summary = await generate_kyc_summary(session_data, history)
    
    # Create the comprehensive transition message based on the DOCX document
    transition_message = f"""🎉 **CONGRATULATIONS! You've officially completed the full Business Planning Phase with Angel inside Founderport!**

You've defined your entrepreneurial profile and shared valuable insights about your experience, goals, and preferences — an incredible milestone in your entrepreneurial journey.

---

## **🧭 Recap of Your Accomplishments**

{kyc_summary}

Angel now has everything needed to guide you through creating your comprehensive business plan.

---

## **⚙️ What Happens Next: Business Planning Phase**

Your completed entrepreneurial profile will now be used to create a fully personalized business planning experience. Here's what we'll build together:

**Your business plan will include:**
- ✅ A fully defined mission and vision statement
- ✅ Market positioning, customer segments, and competitive differentiation
- ✅ Clear pricing and financial projections
- ✅ Comprehensive marketing, legal, and operational frameworks
- ✅ Scalable growth and risk management strategies

**How Angel Will Help:**
- 📊 **Background Research** - I'll conduct research automatically to provide you with industry insights, competitive analysis, and market data
- 💡 **Support** - When you're unsure or want deeper guidance on any question
- ✍️ **Scrapping** - When you have rough ideas that need polishing
- 📝 **Draft** - When you want me to create complete responses based on what I've learned about your business
- 🎯 **Proactive Guidance** - I'll provide both supportive encouragement and constructive coaching at every step

---

## **🎯 Before We Continue**

The Business Planning phase is comprehensive and detailed. This ensures your final business plan is thorough and provides you with a strong starting point for launching your business. The more detailed answers you provide, the better I can help support you to bring your business to life.

**"The best way to predict the future is to create it."** – Peter Drucker

---

## **Ready to Move Forward?**

Once you're ready, we'll begin the Business Planning phase where we'll dive deep into every aspect of your business idea — from your product and market to finances and growth strategy.

**Let's build the business of your dreams together!**

*"The way to get started is to quit talking and begin doing."* – Walt Disney"""
    
    # Check if we should show Accept/Modify buttons
    button_detection = await should_show_accept_modify_buttons(
        user_last_input="KYC completion",
        ai_response=transition_message,
        session_data=session_data
    )
    
    return {
        "reply": transition_message,
        "transition_phase": "KYC_TO_BUSINESS_PLAN",
        "patch_session": {
            "current_phase": "BUSINESS_PLAN_INTRO",  # Intermediate phase before actual questions
            "asked_q": "KYC.19_ACK",  # Keep on KYC until user confirms ready
            "answered_count": session_data.get("answered_count", 0)
        },
        "show_accept_modify": button_detection.get("show_buttons", False),
        "awaiting_confirmation": True  # Signal that we need user to confirm before starting questions
    }

async def generate_kyc_summary(session_data, history):
    """Generate a summary of KYC insights for the transition"""
    # Extract key KYC answers from history
    kyc_insights = []
    
    for msg in history:
        if msg.get('role') == 'assistant' and '[[Q:KYC.' in msg.get('content', ''):
            # This is a KYC question - look for the answer
            question_content = msg.get('content', '')
            # Try to find corresponding user answer in history
            for user_msg in history:
                if user_msg.get('role') == 'user':
                    answer = user_msg.get('content', '').strip()
                    if len(answer) > 10 and answer.lower() not in ['support', 'draft', 'scrapping', 'accept', 'modify']:
                        kyc_insights.append(answer[:150])  # Take first 150 chars of each answer
    
    # Generate summary using the last few meaningful insights
    recent_insights = kyc_insights[-5:] if kyc_insights else []
    
    if not recent_insights:
        return """**Your Entrepreneurial Profile Summary:**

✓ You're ready to take a proactive approach to building your business
✓ You've shared valuable insights about your experience, goals, and preferences
✓ You're prepared to dive deep into the business planning process"""
    
    # Create formatted summary
    summary = "**Your Entrepreneurial Profile Summary:**\n\n"
    
    # Add insights
    if session_data.get('business_name'):
        summary += f"✓ **Business Name**: {session_data.get('business_name')}\n"
    if session_data.get('industry'):
        summary += f"✓ **Industry**: {session_data.get('industry')}\n"
    if session_data.get('location'):
        summary += f"✓ **Location**: {session_data.get('location')}\n"
    if session_data.get('business_experience'):
        summary += f"✓ **Experience Level**: {session_data.get('business_experience')}\n"
    
    summary += "✓ You've completed your full entrepreneurial profile with detailed insights\n"
    summary += "✓ You're ready to transform your vision into a comprehensive business plan"
    
    return summary

async def handle_business_plan_completion(session_data, history):
    """Handle the transition from Business Plan completion to Roadmap phase"""
    
    # Generate comprehensive business plan summary
    business_plan_summary = await generate_business_plan_summary(session_data, history)
    
    # Create the transition message
    transition_message = f"""🎉 **CONGRATULATIONS! Planning Champion Award** 🎉

You've successfully completed your comprehensive business plan! This is a significant milestone in your entrepreneurial journey.

**"Success is not final; failure is not fatal: it is the courage to continue that counts."** – Winston Churchill

---

## **Business Plan Summary Overview**

**Note:** This is a high-level summary of your comprehensive Business Plan. Your complete Business Plan Artifact (the full, detailed document similar to the example provided on 10/10) will be generated and available for download once you proceed to the Roadmap phase.

{business_plan_summary}

---

## **What's Next: Roadmap Generation**

Based on your detailed business plan, I will now generate a comprehensive, actionable launch roadmap that translates your plan into explicit, chronological tasks. This roadmap will include:

**Legal Formation** - Business structure, licensing, permits
**Financial Planning** - Funding strategies, budgeting, accounting setup
**Product & Operations** - Supply chain, equipment, operational processes
**Marketing & Sales** - Brand positioning, customer acquisition, sales processes
**Full Launch & Scaling** - Go-to-market strategy, growth planning

**Research-Backed Recommendations:** The roadmap will be tailored specifically to your business, industry, and location, with research drawn from **Government Sources, Academic Research, and Industry Reports** to provide authoritative, verified guidance.

---

## **Ready to Move Forward?**

Please review your business plan summary above. If everything looks accurate and complete, you can:

**Continue** - Proceed to roadmap generation with full Business Plan Artifact
**Modify** - Adjust any aspects that need refinement

What would you like to do?"""

    # Check if we should show Accept/Modify buttons for Business Plan completion
    button_detection = await should_show_accept_modify_buttons(
        user_last_input="Business Plan completion",
        ai_response=transition_message,
        session_data=session_data
    )

    return {
        "reply": transition_message,
        "web_search_status": {"is_searching": False, "query": None},
        "immediate_response": None,
        "transition_phase": "PLAN_TO_ROADMAP",
        "business_plan_summary": business_plan_summary,
        "show_accept_modify": button_detection.get("show_buttons", False)
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
        # In Business Planning phase, only allow Draft, Support, and Scrapping
        if current_phase == "BUSINESS_PLAN":
            allowed_commands = ["draft", "support", "scrapping:"]
        # In Implementation phase, allow all commands including Kickstart and Contact
        elif current_phase == "IMPLEMENTATION":
            allowed_commands = ["draft", "support", "scrapping:", "kickstart", "who do i contact?"]
        else:
            allowed_commands = ["draft", "support", "scrapping:"]
        
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
- **Draft** - for me to help create an answer based on what you've shared so far
- **Scrapping** - to refine and polish your existing text"""
        
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
- **Scrapping** - to refine and polish your existing text

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
- **Draft** - for me to help create an answer based on what you've shared so far
- **Scrapping** - to refine and polish your existing text"""
        
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
    
    # DISABLED: Critiquing feedback was too aggressive and causing false positives
    # Words like "faster" in "scale faster" were triggering unrealistic assumptions check
    # if user_msg and user_msg.get("content"):
    #     critique_feedback = provide_critiquing_feedback(user_msg["content"], session_data, history)
    #     if critique_feedback:
    #         print(f"🔍 DEBUG - Critiquing feedback triggered: {critique_feedback.get('reply', '')[:100]}...")
    #         return critique_feedback
    
    # Define formatting instruction at the top to avoid UnboundLocalError
    # Get current phase and question info for Business Plan numbering
    current_phase = session_data.get("current_phase", "KYC") if session_data else "KYC"
    asked_q = session_data.get("asked_q", "KYC.01") if session_data else "KYC.01"
    
    FORMATTING_INSTRUCTION = f"""
CRITICAL FORMATTING RULES - FOLLOW EXACTLY:

1. ALWAYS start with a brief acknowledgment (1-2 sentences max)
2. Add a blank line for visual separation
3. Present the question in a clear, structured format

IMPORTANT: The UI automatically displays "Question X" - DO NOT include question numbers in your response!

For YES/NO questions:
"That's great, {user_name}!

Have you started a business before?"

For multiple choice questions:
"That's perfect, {user_name}!

What's your current work situation?"

NOTE: Do NOT list option bullets in your message. The UI displays clickable option buttons.

For rating questions:
"That's helpful, {user_name}!

How comfortable are you with business planning?"

❌ NEVER LIST OPTIONS IN YOUR MESSAGE: 
"What's your current work situation? • Full-time • Part-time • Student..."
"Will your business be primarily: • Online • Brick-and-mortar • Mix of both"

✅ CORRECT - ASK CLEANLY WITHOUT OPTIONS: 
"What's your current work situation?"
"Will your business be primarily?"

CRITICAL: The UI displays option buttons automatically. Do NOT include option lists in your message text.

BUSINESS PLAN SPECIFIC RULES:
• Ask ONE question at a time in EXACT sequential order
• Each question must be on its own line with proper spacing
• NEVER mold user answers into mission, vision, USP without explicit verification
• Do NOT list option bullets in your message - UI shows clickable buttons for multiple-choice questions
• Start with BUSINESS_PLAN.01 and proceed sequentially
• Do NOT jump to later questions or combine multiple questions
• Do NOT provide section summaries or verification steps - just ask the next question
• When user answers, acknowledge briefly (1-2 sentences) and immediately ask the next question
• NEVER include "Question X" in your response - the UI shows it automatically

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
    
    # Handle empty input based on context - preserve current phase state
    if not user_msg.get("content") or user_msg["content"].strip() == "":
        # Get current phase to maintain state on refresh
        current_phase = session_data.get("current_phase", "KYC") if session_data else "KYC"
        
        # If we're in ROADMAP or PLAN_TO_ROADMAP_TRANSITION phase, maintain that state
        if current_phase in ["ROADMAP", "PLAN_TO_ROADMAP_TRANSITION", "ROADMAP_TO_IMPLEMENTATION_TRANSITION"]:
            # Return a message indicating the user is in the roadmap phase
            return {
                "reply": "You're currently in the roadmap phase. Your business plan has been completed and your launch roadmap is ready. Please use the interface to review your roadmap or start implementation.",
                "web_search_status": {"is_searching": False, "query": None},
                "immediate_response": None,
                "patch_session": None
            }
        
        # If we're in BUSINESS_PLAN phase, continue with current question
        elif current_phase == "BUSINESS_PLAN":
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
        
        # Default to "hi" for KYC or initial phases
        user_msg["content"] = "hi"

    user_content = user_msg["content"].strip()
    print(f"🚀 Starting Angel reply generation for: {user_content[:50]}...")
    
    # Check if user just answered the final KYC question BEFORE generating AI response
    if session_data and session_data.get("current_phase") == "KYC":
        current_tag = session_data.get("asked_q", "")
        if current_tag and current_tag.startswith("KYC."):
            try:
                question_num = int(current_tag.split(".")[1])
                # Check if user just answered the final question (19) with any response
                if (question_num >= 19 and 
                    not current_tag.endswith("_ACK") and
                    len(user_content.strip()) > 0):
                    
                    print(f"🎯 User answered final KYC question ({question_num}) - triggering completion immediately BEFORE AI response")
                    # Trigger completion immediately after acknowledgment
                    return await handle_kyc_completion(session_data, history)
            except (ValueError, IndexError):
                pass
    
    # Check if Business Plan phase is complete (question 46 for full flow)
    if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        current_tag = session_data.get("asked_q", "")
        if current_tag and current_tag.startswith("BUSINESS_PLAN."):
            try:
                question_num = int(current_tag.split(".")[1])
                # Check if user just answered the final question (46) with any response
                if (question_num >= 46 and 
                    not current_tag.endswith("_ACK") and
                    len(user_content.strip()) > 0):
                    
                    print(f"🎯 User answered final Business Plan question ({question_num}) - triggering roadmap transition immediately")
                    # Trigger roadmap transition immediately
                    return await handle_business_plan_completion(session_data, history)
            except (ValueError, IndexError):
                pass
    
    # Accept command should be handled by AI naturally, not manually
    # Let the system prompt in constant.py guide question progression
    
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

    # Accept command should be handled by AI to generate next question naturally
    # Do NOT manually increment question numbers or use generate_next_question()
    # Let the AI follow the system prompt from constant.py
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
                # Prevent going beyond KYC.19 (last KYC question)
                if current_phase == "KYC" and current_num >= 19:
                    # Don't increment beyond 19 for KYC
                    next_question_num = "19"
                else:
                    next_question_num = f"{current_num + 1:02d}"
            except (ValueError, IndexError):
                pass
        
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
6. NEVER include "Question X" text in your response - the UI displays it automatically
7. Do NOT ask about business plan drafting or other phases - stay in {current_phase} phase
8. Continue with the next sequential question in the {current_phase} phase
9. NEVER skip questions - ask them in exact sequential order
10. If user provides an answer, acknowledge it briefly and positively (1-2 sentences) - e.g., "Thank you for sharing that!" DO NOT ask the next question yet - the system will show Accept/Modify buttons and only move forward after user clicks Accept
11. If user uses Support/Draft/Scrapping commands, provide help but stay on the same question
12. Do NOT jump to random questions - follow the exact sequence
13. Do NOT list option bullets in your message - the UI displays clickable option buttons
14. Do NOT provide section summaries - just acknowledge answers briefly and wait for user confirmation

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
    
    # Check if we need to provide a section summary BEFORE updating asked_q
    # (Check based on the PREVIOUS question that was just answered, not the next question)
    current_tag_before_update = session_data.get("asked_q") if session_data else None
    section_summary_info = None
    
    # RE-ENABLED: Section summaries with proper timing to prevent question skipping
    # Only show section summary if user just answered a section-ending question
    # Don't show if user clicked Accept (they want to proceed from summary)
    if not is_accept_command and not is_command_response:
        # Check if we just completed a section-ending question
        section_summary_info = check_for_section_summary(current_tag_before_update, session_data, history)
    
    # Extract question tag from reply and update session data BEFORE sequence validation
    # IMPORTANT: Don't update asked_q if we're showing a section summary
    patch_session = {}
    tag_match = re.search(r'\[\[Q:([A-Z_]+\.\d+)\]\]', reply_content)
    if tag_match and session_data and not section_summary_info:
        new_question_tag = tag_match.group(1)
        current_asked_q = session_data.get("asked_q", "")
        
        # Only update if this is a new question (not the same as current)
        if new_question_tag != current_asked_q:
            # Update session data immediately for sequence validation
            session_data["asked_q"] = new_question_tag
            patch_session["asked_q"] = new_question_tag
            print(f"🔧 Updating session asked_q: {current_asked_q} → {new_question_tag}")
    elif section_summary_info:
        print(f"🔒 Section summary active - NOT updating asked_q (staying at {current_tag_before_update})")
    
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
    
    if section_summary_info:
        print(f"🎯 SECTION SUMMARY TRIGGERED for {section_summary_info['section_name']} at question {current_tag_before_update}")
        
        # CRITICAL: Don't let the question number increment during section summary
        # The summary shows AFTER answering the last question of a section
        # We stay on the same question number until user accepts the summary
        
        # Add section summary requirements to the system prompt
        summary_instruction = f"""
IMPORTANT: You have just completed {section_summary_info['section_name']} section. 
You MUST provide a comprehensive section summary that includes:

1. **Summary**: Recap the key information provided in this section
2. **Educational Insights**: Provide valuable insights about this business area
3. **Critical Considerations**: Highlight important watchouts and considerations for this business type
4. **Verification Request**: Ask user to verify the information before proceeding

Use this EXACT format:
"🎯 **{section_summary_info['section_name']} Section Complete**

**Summary of Your Information:**
[Recap key points from this section]

**Educational Insights:**
[Provide valuable business insights related to this section]

**Critical Considerations:**
[Highlight important watchouts and things to consider]

**Ready to Continue?**
Please confirm that this information is accurate before we move to the next section. You can either accept this summary and continue, or let me know what you'd like to modify.

[[ACCEPT_MODIFY_BUTTONS]]"

CRITICAL: 
- End your response with [[ACCEPT_MODIFY_BUTTONS]] to trigger the Accept/Modify buttons
- Do NOT ask the next question immediately
- Do NOT include any question tags like [[Q:BUSINESS_PLAN.XX]] in this response
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
        
        # IMPORTANT: Clear any question tags from the summary response to prevent asked_q from updating
        reply_content = re.sub(r'\[\[Q:[A-Z_]+\.\d+\]\]', '', reply_content)
        print(f"🔒 Section summary generated - keeping asked_q at {current_tag_before_update} until user accepts")
    
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
    
    
    # Clean up internal tags before sending to user
    # Remove [[ACCEPT_MODIFY_BUTTONS]] tag - it's only for backend detection, not display
    reply_content = reply_content.replace("[[ACCEPT_MODIFY_BUTTONS]]", "").strip()
    
    return {
        "reply": reply_content,
        "web_search_status": web_search_status,
        "immediate_response": immediate_response,
        "patch_session": patch_session if patch_session else None,
        "show_accept_modify": button_detection.get("show_buttons", False)
    }

async def handle_draft_command(reply, history, session_data=None):
    """Handle the Draft command with research-backed comprehensive response generation"""
    # Extract context from conversation history
    context_summary = extract_conversation_context(history)
    business_context = extract_business_context_from_history(history)
    
    # Get current question context for more targeted responses
    current_question = get_current_question_context(history, session_data)
    
    # Conduct web search for research-backed drafts (for specific question types)
    business_name = business_context.get("business_name", "business")
    industry = business_context.get("industry", "business")
    location = business_context.get("location", "")
    question_topic = get_question_topic(current_question)
    
    # Trigger research for data-heavy questions
    research_topics = ["competitor", "competitive analysis", "startup costs", "operational requirements", 
                       "staffing needs", "target market", "sales projections", "financial planning",
                       "expenses", "pricing", "market", "customer acquisition"]
    
    research_results = None
    if any(topic in question_topic.lower() for topic in research_topics):
        research_query = f"{industry} {question_topic} {location} data statistics 2024"
        print(f"🔍 Draft command - Conducting research: {research_query}")
        research_results = await conduct_web_search(research_query)
    
    # Generate draft content based on conversation history, question, and research
    draft_content = await generate_draft_content(history, business_context, current_question, research_results)
    
    # Create a comprehensive draft response with clear heading
    draft_response = f"Here's a research-backed draft for you:\n\n{draft_content}\n\n"
    
    return draft_response

def get_current_question_context(history, session_data=None):
    """Extract the current question context from the most recent assistant message or session data"""
    
    # First, try to get current question from session data if available
    if session_data and session_data.get('asked_q'):
        asked_q = session_data.get('asked_q')
        print(f"🔍 DEBUG - Found current question from session: {asked_q}")
        
        # Look for the actual question content in recent history that matches this question tag
        for msg in reversed(history[-10:]):  # Look at last 10 messages
            if msg.get('role') == 'assistant' and msg.get('content'):
                content = msg['content']
                # Check if this message contains the current question tag
                if f'[[Q:{asked_q}]]' in content:
                    print(f"🔍 DEBUG - Found matching question content for {asked_q}")
                    return content
        
        # If no matching content found, return the question tag for context
        print(f"🔍 DEBUG - No matching content found, returning question tag: {asked_q}")
        return f"Current question: {asked_q}"
    
    # Fallback: Look for the most recent assistant message that contains a question tag
    for msg in reversed(history[-8:]):  # Look at last 8 messages to find the actual question
        if msg.get('role') == 'assistant' and msg.get('content'):
            content = msg['content'].lower()
            # Skip command responses and look for actual questions
            if any(command in content for command in ['here\'s a draft', 'let\'s work through this', 'here\'s a refined version', 'verification:', 'here\'s what i\'ve captured']):
                continue
            # Look for question tags or question indicators
            if '[[' in content and ']]' in content and any(indicator in content for indicator in ['what', 'how', 'when', 'where', 'why', 'do you', 'are you', 'can you']):
                question_text = content
                print(f"🔍 DEBUG - Found current question from history: {question_text[:200]}...")
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

async def generate_draft_content(history, business_context, current_question="", research_results=None):
    """Generate research-backed draft content based on conversation history"""
    # Extract recent messages (both user and assistant) to understand context
    recent_messages = []
    for msg in history[-8:]:  # Look at last 8 messages (4 exchanges)
        if msg.get('content'):
            recent_messages.append(msg['content'])
    
    # Debug logging
    print(f"🔍 DEBUG - Recent messages for draft context: {recent_messages}")
    print(f"🔍 DEBUG - Research results available for draft: {bool(research_results)}")
    
    # Generate contextual draft based on what they've been discussing
    if not recent_messages:
        return "Based on our conversation, here's a draft response that captures the key points we've discussed and provides a comprehensive answer to your current question."
    
    # Look for key topics in recent messages (both questions and responses)
    recent_text = " ".join(recent_messages).lower()
    print(f"🔍 DEBUG - Recent text for draft analysis: {recent_text[:200]}...")
    
    # Use the current_question parameter if provided, otherwise extract from history
    if not current_question:
        current_question = get_current_question_context(history, session_data)
    
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
    
    # Use AI to generate a comprehensive, personalized, research-backed draft
    research_section = ""
    if research_results:
        research_section = f"""
    
    📊 RESEARCH DATA (INCORPORATE INTO DRAFT):
        {research_results}
    
    Use this research to provide data-driven, factual content with citations.
    """
    
    draft_prompt = f"""
    ⚠️ CRITICAL CONTEXT - READ FIRST:
        This business is in the {industry.upper()} INDUSTRY operating as a {business_type.upper()}.
    ALL draft content must be 100% specific to {industry.upper()} businesses - NOT education, NOT technology, NOT consulting.
    Use ONLY {industry.upper()} industry examples, terminology, and context.
    {research_section}
    
    Create a comprehensive, detailed, research-backed draft answer for this business question: "{current_question}"
    
    Business Context (PRIMARY IDENTIFIERS):
    - Business Name: {business_name}
    - PRIMARY INDUSTRY: {industry.upper()} ⭐ (THIS IS THE CORE BUSINESS TYPE)
    - Business Structure: {business_type}
    - Location: {location}
    
    Previous Answers and Context:
    {' | '.join(previous_answers[-3:]) if previous_answers else 'No previous context available'}
    
    Generate a complete, well-structured draft answer that:
        1. Directly answers the question with specific, data-backed content for a {industry.upper()} business
    2. Incorporates research findings, statistics, and data when available
    3. Cites sources and data points from research findings
    4. Is personalized to {business_name} in the {industry.upper()} industry
    5. Considers the {location} market and local factors with actual data
    6. Provides concrete details and examples from the {industry.upper()} industry (not generic advice)
    7. Is appropriate for a {business_type} business structure
    8. Uses information from previous answers when relevant
    9. Includes bullet points or numbered lists for clarity
    10. Is comprehensive enough to be used as-is (500-700 words)
    11. NEVER mentions unrelated industries - stay focused on {industry.upper()}
    
    Structure the draft with clear sections like:
        - Main answer/core content for {industry.upper()} business (with data)
    - Key points or features with statistics (use bullet points)
    - Research-backed insights and market data
    - Specific considerations for the {industry} business
    - Next steps or recommendations
    - Sources cited (if research data was provided)
    
    Make this a complete, polished, research-backed draft that the user can accept and use immediately. Be specific and detailed, not generic.
    REMEMBER: This is a {industry.upper()} business - all examples, features, and recommendations must be relevant to {industry.upper()}.
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": draft_prompt}],
            temperature=0.3,
            max_tokens=2000  # Increased for comprehensive research-backed draft responses
        )
        
        ai_draft = response.choices[0].message.content
        print(f"✅ Draft content generated with {len(ai_draft)} characters{' (with research)' if research_results else ''}")
        return ai_draft
    except Exception as e:
        print(f"❌ AI draft generation failed: {e}, falling back to template-based drafts")
        # Fallback with research if available
        if research_results:
            return f"""Based on research findings for {business_name} in the {industry} industry:

{research_results}

This data can help you craft a comprehensive answer for your {location} market."""
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
        return await generate_sales_projection_draft(business_context, current_question)
    
    elif any(keyword in current_question for keyword in ['startup costs', 'estimated startup costs', 'one-time expenses', 'initial costs', 'launch costs']):
        return await generate_startup_costs_table_draft(business_context, current_question)
    
    elif any(keyword in current_question for keyword in ['monthly expenses', 'monthly operating expenses', 'recurring costs', 'operating expenses']):
        return await generate_monthly_expenses_draft(business_context, current_question)
    
    elif any(keyword in current_question for keyword in ['customer acquisition cost', 'acquisition cost', 'customer acquisition']):
        return await generate_customer_acquisition_cost_draft(business_context, current_question)
    
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
        return generate_sales_projection_draft(business_context, current_question)
    
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
    current_question = get_current_question_context(history, session_data)
    
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
    ⚠️ CRITICAL CONTEXT - READ FIRST:
        This business is in the {industry.upper()} INDUSTRY operating as a {business_type.upper()}.
    ALL refinements must be 100% specific to {industry.upper()} businesses - NOT education, NOT technology, NOT consulting.
    Use ONLY {industry.upper()} industry examples, insights, and terminology.
    
    Take this user's rough notes/ideas and refine them into a comprehensive, well-structured answer for the question: "{current_question}"
    
    User's Notes/Ideas:
    "{cleaned_notes}"
    
    Business Context (PRIMARY IDENTIFIERS):
    - Business Name: {business_name}
    - PRIMARY INDUSTRY: {industry.upper()} ⭐ (THIS IS THE CORE BUSINESS TYPE)
    - Business Structure: {business_type}
    - Location: {location}
    
    Your task:
        1. Take the user's rough ideas and refine them into polished, professional content for a {industry.upper()} business
    2. Expand on their ideas with industry-specific insights for {industry.upper()} only
    3. Add relevant details and context appropriate for a {business_type} in {location}
    4. Structure the content clearly with sections and bullet points
    5. Keep the user's core ideas but make them more comprehensive and actionable
    6. Add strategic recommendations that build on their initial thoughts
    7. Make it 300-500 words of refined, detailed content
    8. NEVER mentions unrelated industries - stay focused on {industry.upper()}
    
    Structure your refined version with:
    **Refined Core Concept:**
    [Their idea, polished and expanded for {industry.upper()} business]
    
    **{industry.upper()} Industry-Specific Application:**
    [How this applies to the {industry.upper()} industry specifically]
    
    **Strategic Recommendations for {industry.upper()} Business:**
    [3-5 specific recommendations building on their ideas]
    
    **Implementation Steps:**
    [4-6 concrete steps they can take]
    
    **Key Considerations for {industry.upper()}:**
    [2-3 important factors to consider]
    
    Make this a comprehensive refinement that takes their rough ideas and turns them into polished, actionable content.
    REMEMBER: This is a {industry.upper()} business - all refinements must be relevant to {industry.upper()}.
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
    ⚠️ CRITICAL CONTEXT - READ FIRST:
        This business is in the {industry.upper()} INDUSTRY operating as a {business_type.upper()}.
    ALL analysis must be 100% specific to {industry.upper()} businesses - NOT education, NOT technology, NOT consulting.
    Use ONLY {industry.upper()} industry examples, trends, and insights.
    
    Generate a comprehensive, refined analysis that helps answer this business question: "{current_question}"
    
    Business Context (PRIMARY IDENTIFIERS):
    - Business Name: {business_name}
    - PRIMARY INDUSTRY: {industry.upper()} ⭐ (THIS IS THE CORE BUSINESS TYPE)
    - Business Structure: {business_type}
    - Location: {location}
    
    Previous Context:
    {' | '.join(previous_answers[-3:]) if previous_answers else 'No previous context available'}
    
    Research Notes (if provided):
    {notes if notes else 'No specific research notes provided'}
    
    Create a detailed, refined analysis that:
        1. Synthesizes relevant information from the {industry.upper()} business context
    2. Provides industry-specific insights for the {industry.upper()} sector only
    3. Considers market dynamics in {location}
    4. Offers strategic recommendations appropriate for a {business_type}
    5. Includes current {industry.upper()} industry trends and best practices (2024-2025)
    6. Provides actionable next steps
    7. Is comprehensive and detailed (400-500 words)
    8. NEVER mentions unrelated industries - stay focused on {industry.upper()}
    
    Structure your analysis with these sections:
    **Business Context Analysis:**
    [Overview of the {industry.upper()} business and how it relates to the question]
    
    **{industry.upper()} Industry-Specific Insights:**
    [3-4 insights specific to the {industry.upper()} industry]
    
    **Market Opportunities in {industry.upper()}:**
    [2-3 opportunities in the {location} market for {industry} businesses]
    
    **Strategic Recommendations for {industry.upper()} Business:**
    [4-5 specific, actionable recommendations]
    
    **Implementation Priorities:**
    [3-4 priority actions to take]
    
    **Key Success Factors for {industry.upper()}:**
    [2-3 factors critical for success in {industry}]
    
    Make this comprehensive, strategic, and highly actionable.
    REMEMBER: This is a {industry.upper()} business - all analysis must be relevant to {industry.upper()}.
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
    """Handle the Support command with aggressive web search research"""
    # Extract business context for verification
    business_context = extract_business_context_from_history(history)
    
    # Get current question context for more targeted responses
    current_question = get_current_question_context(history, session_data)
    
    # ALWAYS conduct web search for Support command
    business_name = business_context.get("business_name", "business")
    industry = business_context.get("industry", "business")
    location = business_context.get("location", "")
    
    # Create targeted research query
    question_topic = get_question_topic(current_question)
    research_query = f"{industry} {question_topic} {location} 2024 2025"
    
    print(f"🔍 Support command - Conducting research: {research_query}")
    
    # Conduct comprehensive web search
    research_results = await conduct_web_search(research_query)
    
    # Generate support content based on conversation history, question, AND research
    support_content = await generate_support_content(history, business_context, current_question, research_results)
    
    support_response = f"Let me help you with research-backed insights:\n\n{support_content}\n\n"
    
    return support_response

async def generate_support_content(history, business_context, current_question="", research_results=None):
    """Generate support content with research-backed insights and citations"""
    # Extract recent messages (both user and assistant) to understand context
    recent_messages = []
    for msg in history[-8:]:  # Look at last 8 messages (4 exchanges)
        if msg.get('content'):
            recent_messages.append(msg['content'])
    
    # Debug logging
    print(f"🔍 DEBUG - Recent messages for support context: {recent_messages}")
    print(f"🔍 DEBUG - Research results available: {bool(research_results)}")
    
    # Generate contextual support based on what they've been discussing
    if not recent_messages:
        return "I'm here to provide comprehensive support for your business planning journey. Let me help you think through the current question with additional insights and guidance."
    
    # Look for key topics in recent messages (both questions and responses)
    recent_text = " ".join(recent_messages).lower()
    print(f"🔍 DEBUG - Recent text for analysis: {recent_text[:200]}...")
    
    # Use the current_question parameter if provided, otherwise extract from history
    if not current_question:
        current_question = get_current_question_context(history, session_data)
    
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
    
    # Generate dynamic support using AI model with research results and citations
    research_section = ""
    if research_results:
        research_section = f"""
    
    📊 RESEARCH FINDINGS (USE THESE IN YOUR RESPONSE):
        {research_results}
    
    CRITICAL: Incorporate the research findings above into your response. Cite specific data points, statistics, and sources mentioned.
    """
    
    support_prompt = f"""
    ⚠️ CRITICAL CONTEXT - READ FIRST:
        This business is in the {industry.upper()} INDUSTRY operating as a {business_type.upper()}.
    ALL guidance must be 100% specific to {industry.upper()} businesses - NOT education, NOT technology, NOT consulting.
    Focus EXCLUSIVELY on {industry.upper()} industry challenges, examples, trends, and best practices.
    {research_section}
    
    🎯 CURRENT QUESTION BEING ADDRESSED:
        "{current_question}"
    
    ⚠️ CRITICAL REQUIREMENT: Your entire response must be DIRECTLY RELEVANT to answering this specific question. Do not provide general business advice or information that doesn't directly help answer this question. Stay focused and on-topic.
    
    Business Context (PRIMARY IDENTIFIERS):
    - Business Name: {business_name}
    - PRIMARY INDUSTRY: {industry.upper()} ⭐ (THIS IS THE CORE BUSINESS TYPE)
    - Business Structure: {business_type}
    - Location: {location}
    
    Previous Context from Conversation:
    {' | '.join(previous_answers[-3:]) if previous_answers else 'No previous context available'}
    
    Provide extremely detailed, research-backed guidance that DIRECTLY ANSWERS the current question:
        1. Incorporates actual research findings, statistics, and data from authoritative sources
    2. Cites specific sources and URLs when available from the research
    3. Is highly specific to the {industry.upper()} industry with real examples and current data
    4. Considers the {location} market dynamics with local data when available
    5. Is appropriate for a {business_type} with practical, evidence-based implementation steps
    6. Includes 5-7 concrete, actionable steps backed by research and industry data
    7. References current {industry.upper()} industry trends, statistics, and best practices (2024-2025)
    8. Addresses common challenges specific to {industry.upper()} businesses with data-driven solutions
    9. Provides strategic insights backed by research and market data
    10. ⚠️ STAYS FOCUSED on the current question - do not include unrelated information
    11. CITES SOURCES throughout the response when referencing data or statistics
    
    Structure your response with:
        **Research-Backed Insights for {industry.upper()}**
    [Key findings from research with citations]
    
    **Understanding the Question**
    [What this question means for their {industry.upper()} business, with relevant data]
    
    **Industry Data & Statistics**
    [Specific data points, trends, and statistics for {industry.upper()} with sources]
    
    **Practical Action Steps (Evidence-Based)**
    [5-7 numbered, detailed action steps backed by research and data]
    
    **Common Challenges & Data-Driven Solutions**
    [2-3 challenges {industry} businesses face with research-backed solutions]
    
    **Best Practices (Industry Research)**
    [3-4 best practices from authoritative sources and industry leaders]
    
    **Sources & Citations**
    [List all sources referenced with URLs when available]
    
    Make the guidance extremely comprehensive, detailed, and research-backed. Aim for 500-700 words of rich, valuable, cited content.
    REMEMBER: This is a {industry.upper()} business - keep all examples, insights, and recommendations relevant to {industry.upper()}.
    CITE YOUR SOURCES throughout the response using the research findings provided.
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": support_prompt}],
            temperature=0.3,
            max_tokens=2000  # Increased for comprehensive research-backed responses with citations
        )
        
        generated_content = response.choices[0].message.content
        print(f"✅ Support content generated with {len(generated_content)} characters")
        return generated_content
    except Exception as e:
        print(f"❌ Dynamic support generation failed: {e}")
        # Fallback to basic guidance with research if available
        if research_results:
            return f"""Based on research findings for your {industry} business:

{research_results}

Let me help you apply this to your specific situation in {location}. Consider how this data relates to your {business_type} structure and the unique aspects of your {industry} business."""
        else:
            return f"Let me help you think through this question for your {industry} business. Consider the specific challenges and opportunities in the {industry} sector, especially in {location}. Focus on how this relates to your {business_type} structure and the unique aspects of your industry."
    
    

async def handle_draft_more_command(reply, history, session_data=None):
    """Handle the Draft More command to create additional content"""
    # Extract business context for verification
    business_context = extract_business_context_from_history(history)
    
    # Get current question context for more targeted responses
    current_question = get_current_question_context(history, session_data)
    
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
    ⚠️ CRITICAL CONTEXT - READ FIRST:
        This business is in the {industry.upper()} INDUSTRY operating as a {business_type.upper()}.
    ALL enhanced content must be 100% specific to {industry.upper()} businesses - NOT education, NOT technology, NOT consulting.
    Use ONLY {industry.upper()} industry examples, innovations, and insights.
    
    The user requested "Draft More" - they want additional, enhanced content on top of what was already provided.
    
    Current Question: "{current_question}"
    
    Business Context (PRIMARY IDENTIFIERS):
    - Business Name: {business_name}
    - PRIMARY INDUSTRY: {industry.upper()} ⭐ (THIS IS THE CORE BUSINESS TYPE)
    - Business Structure: {business_type}
    - Location: {location}
    
    Previous Context:
    {' | '.join(previous_answers[-3:]) if previous_answers else 'No previous context available'}
    
    Generate ENHANCED, ADDITIONAL content that:
        1. Takes the original answer to the next level with MORE detail for {industry.upper()} businesses
    2. Adds 3-5 UNIQUE angles or perspectives specific to {industry.upper()} industry
    3. Provides ADVANCED strategic insights specific to {industry.upper()} in {location}
    4. Includes innovative ideas and creative approaches for {industry} businesses
    5. Offers cutting-edge {industry.upper()} industry trends and best practices (2024-2025)
    6. Makes it stand out with unique value propositions
    7. Is comprehensive (400-600 words) and highly actionable
    8. NEVER mentions unrelated industries - stay focused on {industry.upper()}
    
    Structure your enhanced draft with:
    **Enhanced Main Content:**
    [Take the original concept and elevate it with unique insights for {industry.upper()}]
    
    **Unique Angles & Innovation for {industry.upper()}:**
    [3-5 creative approaches specific to {industry} businesses]
    
    **Advanced Strategic Insights for {industry.upper()}:**
    [Deep industry-specific strategies for {industry.upper()}]
    
    **Implementation Roadmap:**
    [Detailed 5-7 step plan with specifics]
    
    **Competitive Edge Factors in {industry.upper()}:**
    [What makes this approach uniquely powerful for {industry} businesses]
    
    Make this draft MORE creative, MORE detailed, and MORE strategic than a standard response. Think outside the box!
    REMEMBER: This is a {industry.upper()} business - all enhanced content must be relevant to {industry.upper()}.
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
    """Extract business context information from conversation history with weighted priority"""
    business_context = {
        "business_name": "",
        "industry": "",
        "location": "",
        "business_type": "",
        "target_market": "",
        "business_idea": ""
    }
    
    # Track weights for prioritization (higher = more authoritative)
    context_weights = {
        "business_name": 0,
        "industry": 0,
        "location": 0,
        "business_type": 0,
        "target_market": 0,
        "business_idea": 0
    }
    
    print(f"🔍 DEBUG - Extracting business context from {len(history)} messages with weighted priority")
    
    # NO MORE HARDCODED OVERRIDES - Let AI naturally detect business type from conversation
    # Removed plumbing-specific override logic - system now works for ALL business types dynamically
    
    # First pass: Identify KYC questions to prioritize their answers
    kyc_question_indices = {}
    for i, msg in enumerate(history):
        if msg["role"] == "assistant":
            content = msg["content"]
            if "[[Q:KYC.11]]" in content:  # Industry question
                kyc_question_indices["industry"] = i
                print(f"🔍 DEBUG - Found KYC.11 (industry question) at index {i}")
            elif "[[Q:KYC.16]]" in content:  # Business structure question
                kyc_question_indices["business_type"] = i
                print(f"🔍 DEBUG - Found KYC.16 (business type question) at index {i}")
            elif "[[Q:KYC.10]]" in content:  # Location question
                kyc_question_indices["location"] = i
                print(f"🔍 DEBUG - Found KYC.10 (location question) at index {i}")
    
    # Extract from all messages (not just recent ones)
    for i, msg in enumerate(history):
        if msg["role"] == "user":
            content = msg["content"]
            content_lower = content.lower()
            
            print(f"🔍 DEBUG - Message {i}: {content[:100]}...")
            
            # Check if this is a response to a KYC question (HIGHEST PRIORITY - weight 100)
            is_kyc_industry_answer = "industry" in kyc_question_indices and i == kyc_question_indices["industry"] + 1
            is_kyc_business_type_answer = "business_type" in kyc_question_indices and i == kyc_question_indices["business_type"] + 1
            is_kyc_location_answer = "location" in kyc_question_indices and i == kyc_question_indices["location"] + 1
            
            # Extract industry from KYC.11 answer - Use user's EXACT answer
            if is_kyc_industry_answer and len(content.strip()) > 2:
                # Use the user's exact answer - no keyword matching, no hardcoding
                industry_answer = content.strip()
                business_context["industry"] = industry_answer
                context_weights["industry"] = 100
                print(f"🔍 DEBUG - ⭐ HIGHEST PRIORITY: KYC.11 industry answer (EXACT): '{industry_answer}' (weight 100)")
            
            # Extract business type from KYC.16 answer (HIGHEST PRIORITY)
            if is_kyc_business_type_answer and len(content.strip()) > 2:
                business_type_answer = content.strip()
                business_context["business_type"] = business_type_answer
                context_weights["business_type"] = 100
                print(f"🔍 DEBUG - ⭐ HIGHEST PRIORITY: KYC.16 business type answer: '{business_type_answer}' (weight 100)")
            
            # Extract location from KYC.10 answer (HIGHEST PRIORITY)
            if is_kyc_location_answer and len(content.strip()) > 2:
                location_answer = content.strip()
                business_context["location"] = location_answer
                context_weights["location"] = 100
                print(f"🔍 DEBUG - ⭐ HIGHEST PRIORITY: KYC.10 location answer: '{location_answer}' (weight 100)")
            
            # Extract business name - prioritize domain names and longer names over short responses
            # First check for domain-like names (highest priority - weight 80)
            if "." in content and any(ext in content_lower for ext in [".com", ".net", ".org", ".co"]):
                potential_name = content.strip()
                command_words = ["support", "draft", "scrapping", "scraping", "accept", "modify", "ok", "okay", "yes", "no", "small business", "corporation", "llc", "inc", "sole proprietorship"]
                # Limit business name to reasonable length to prevent long content
                if len(potential_name) > 5 and len(potential_name) < 50 and potential_name.lower() not in command_words:
                    if context_weights["business_name"] < 80:
                        business_context["business_name"] = potential_name
                        context_weights["business_name"] = 80
                        print(f"🔍 DEBUG - Found domain business name: {potential_name} (weight 80)")
            
            # Then look for patterns like "my business is", "company name", etc. (weight 70)
            elif context_weights["business_name"] < 70 and any(phrase in content_lower for phrase in ["my business is", "company name", "startup name", "business name", "what is your business name"]):
                # Extract the name after these phrases
                for phrase in ["my business is", "company name", "startup name", "business name", "what is your business name"]:
                    if phrase in content_lower:
                        parts = content.split(phrase)
                        if len(parts) > 1:
                            potential_name = parts[1].strip().split()[0]
                            if len(potential_name) > 2:
                                business_context["business_name"] = potential_name
                                context_weights["business_name"] = 70
                                print(f"🔍 DEBUG - Found business name: {potential_name} (weight 70)")
                                break
            
            # Finally look for direct business name responses (weight 50)
            elif context_weights["business_name"] < 50 and len(content.strip()) < 100 and not any(word in content_lower for word in ["yes", "no", "maybe", "i", "my", "the", "a", "an"]) and not any(char.isdigit() for char in content.strip()):
                # If it's a short response that looks like a business name (and doesn't contain numbers)
                potential_name = content.strip()
                # Exclude command words and common responses
                command_words = ["support", "draft", "scrapping", "scraping", "accept", "modify", "ok", "okay", "yes", "no", "small business", "corporation", "llc", "inc", "sole proprietorship", "sure", "financial", "personal savings"]
                # Allow domain names and business names with dots, hyphens, etc.
                if len(potential_name) > 2 and potential_name.lower() not in command_words:
                    # Check if it looks like a business name (contains letters and possibly dots, hyphens)
                    if any(c.isalpha() for c in potential_name) and not potential_name.lower() in ["small business", "corporation", "llc", "inc"]:
                            business_context["business_name"] = potential_name
                            context_weights["business_name"] = 50
                            print(f"🔍 DEBUG - Found direct business name: {potential_name} (weight 50)")
            
            # Extract industry from natural conversation - use exact user words, no keyword lists
            # Only as fallback if KYC answer not available (weight < 100)
            if context_weights["industry"] < 50:
                # Look for business/industry mentions in user's own words
                if any(phrase in content_lower for phrase in ["business", "company", "startup", "industry", "service"]):
                    # Extract the full phrase - let AI understand it later
                    if len(content.strip()) > 5 and len(content.strip()) < 100:
                        # Use user's exact words as industry descriptor
                        business_context["industry"] = content.strip()
                        context_weights["industry"] = 20
                        print(f"🔍 DEBUG - Using user's exact description as industry: '{content.strip()[:50]}' (weight 20)")
            
            # Extract location information - Only if not from KYC (weight < 100)
            if context_weights["location"] < 100:
                # Look for location mentions
                if any(phrase in content_lower for phrase in ["located in", "based in", "karachi", "lahore", "islamabad", "city", "location"]):
                    # Look for city names or location patterns
                    locations = ["karachi", "lahore", "islamabad", "rawalpindi", "faisalabad", "multan", "peshawar", "quetta", "sialkot", "gujranwala"]
                    for location in locations:
                        if location in content_lower:
                            if context_weights["location"] < 50:
                                business_context["location"] = location.title()
                                context_weights["location"] = 50
                                print(f"🔍 DEBUG - Found location: {location} (weight 50)")
                            break
                    # If no specific city found, look for "located in" pattern
                    if context_weights["location"] < 50 and "located in" in content_lower:
                        parts = content.split("located in")
                        if len(parts) > 1:
                            potential_location = parts[1].strip().split()[0]
                            if len(potential_location) > 2:
                                business_context["location"] = potential_location.title()
                                context_weights["location"] = 50
                                print(f"🔍 DEBUG - Found location from pattern: {potential_location} (weight 50)")
            
            # Extract business type - Only if not from KYC (weight < 100)
            if context_weights["business_type"] < 100:
                # Look for business type mentions
                if any(phrase in content_lower for phrase in ["business type", "type of business", "startup", "company", "corporation", "llc", "partnership"]):
                    business_types = ["startup", "company", "corporation", "llc", "partnership", "sole proprietorship", "nonprofit", "franchise"]
                    for biz_type in business_types:
                        if biz_type in content_lower:
                            if context_weights["business_type"] < 50:
                                business_context["business_type"] = biz_type
                                context_weights["business_type"] = 50
                                print(f"🔍 DEBUG - Found business type: {biz_type} (weight 50)")
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
    print(f"🔍 DEBUG - Context weights: {context_weights}")
    print(f"⭐ PRIORITY SUMMARY - Industry: '{business_context.get('industry', 'N/A')}' (weight: {context_weights['industry']}), Business Type: '{business_context.get('business_type', 'N/A')}' (weight: {context_weights['business_type']})")
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
    """
    Handle the transition from Roadmap completion to Implementation phase
    Based on the "Transition Roadmap to Implementation - Descriptive.docx" document
    """
    
    # Extract business context from session data
    business_name = session_data.get('business_name', 'Your Business')
    industry = session_data.get('industry', 'general business')
    location = session_data.get('location', 'United States')
    
    # Generate roadmap summary
    roadmap_summary = f"""**Your Completed Roadmap Summary:**

✅ **Legal Formation** - Complete
✅ **Financial Planning** - Complete
✅ **Product & Operations** - Defined
✅ **Marketing** - Launched
✅ **Launch & Scaling** - Finalized"""
    
    # Create comprehensive transition message based on DOCX document
    transition_message = f"""[Confetti animation 🎊 floats upward across the screen]

🏅 **EXECUTION READY BADGE UNLOCKED** 🏅

*For completing your full roadmap journey and preparing for business launch.*

---

**{business_name}, that's incredible.** You've completed your full Launch Roadmap. Every milestone — from formation to marketing — checked off. You're now ready to bring {business_name} fully to life.

---

## **📋 Your Completed Roadmap Summary**

{roadmap_summary}

You've officially built the foundation. Now let's execute with precision and confidence.

---

## **🚀 Next Phase: Implementation — Bringing {business_name} to Life**

What you've done so far isn't just planning — it's progress. Now it's time to step into the **Implementation Phase** — where we turn every plan into real, measurable action.

I'll stay with you, just as before, guiding you through each task one at a time — whether it's filing documents, managing outreach, or setting up your first customer channel.

---

## **⚙️ How Angel Helps in Implementation Phase**

Here's what you can expect in this phase:

| **Function** | **Description** |
|--------------|----------------|
| **Advice & Tips** | I'll share focused, practical insights to guide every action |
| **Kickstart** | I can complete parts of tasks for you — like drafting outreach emails or setting up a checklist |
| **Help** | Ask for deep, detailed guidance whenever you hit a roadblock |
| **Who do I contact?** | I'll connect you with trusted, relevant professionals or providers near you in {location} |
| **Dynamic Feedback** | I'll notice when tasks look incomplete or off-track and help correct them quickly |

---

## **📊 Implementation Progress Tracking**

Just like before, you'll have a visual tracker — so you can watch your real progress, not just your plans. Each task you complete gets you closer to full launch.

**[Implementation Progress: 0% → Ready to Begin]**

---

## **💪 Take a Moment to Recognize Your Journey**

{business_name}, before we dive in, take a second to recognize how far you've come:

✅ You started with an idea
✅ You've built a comprehensive plan
✅ You've created a detailed roadmap
✅ Now, we'll bring it all to life — step by step

---

## **🎯 Ready to Begin Implementation?**

When you're ready, we'll show you the first real-world action to take — and we'll tackle it together.

**"What you've done so far isn't just planning — it's progress. Now let's execute with precision and confidence."**

---

*This implementation process is tailored specifically to your "{business_name}" business in the {industry} industry, located in {location}. Every recommendation is designed to help you build the business of your dreams.*"""
    
    # Check if we should show Accept/Modify buttons
    button_detection = await should_show_accept_modify_buttons(
        user_last_input="Roadmap completion",
        ai_response=transition_message,
        session_data=session_data
    )
    
    return {
        "reply": transition_message,
        "transition_phase": "ROADMAP_TO_IMPLEMENTATION",
        "patch_session": {
            "current_phase": "IMPLEMENTATION",
            "asked_q": "IMPLEMENTATION.01",
            "answered_count": 0
        },
        "show_accept_modify": button_detection.get("show_buttons", False),
        "awaiting_confirmation": True  # Signal that we need user to confirm before starting implementation tasks
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
async def generate_startup_costs_table_draft(business_context, current_question):
    """Generate dynamic, AI-powered startup costs table for ANY business type"""
    industry = business_context.get("industry", "your industry")
    business_name = business_context.get("business_name", "your business")
    location = business_context.get("location", "your location")
    business_type = business_context.get("business_type", "service")
    
    # Use AI to generate industry-specific, location-aware startup costs
    prompt = f"""You are a business finance expert. Generate a comprehensive startup costs table for a {industry} business named "{business_name}" in {location}.

CONTEXT:
- Business Type: {business_type}
- Industry: {industry}
- Location: {location}

REQUIREMENTS:
1. Include industry-specific equipment, tools, and technology
2. Include all necessary licenses and certifications specific to {industry}
3. Adjust costs realistically for {location}'s cost of living
4. Provide 4-6 main categories with specific line items
5. Give realistic cost ranges (minimum - maximum)
6. Add helpful, industry-specific notes
7. Calculate and show total estimated costs

FORMAT EXACTLY AS BELOW:

**Startup Costs Breakdown**

| Category | Item | Estimated Cost | Notes |
|----------|------|----------------|-------|
| **[Category 1]** | | | |
| | [Specific item] | $X,XXX - $X,XXX | [Helpful note] |
| | [Specific item] | $X,XXX - $X,XXX | [Helpful note] |
| **[Category 2]** | | | |
| | [Specific item] | $X,XXX - $X,XXX | [Helpful note] |
[... continue for all categories ...]

**Total Estimated Startup Costs: $XX,XXX - $XX,XXX**

*Note: [Add location and industry-specific context]*

Be specific to {industry}, not generic. Include actual industry requirements."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1200
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating startup costs: {e}")
        # Fallback if AI fails
        return f"""Based on your {industry} business in {location}, consider these startup cost categories:

**Key Startup Cost Areas:**
- Industry-specific equipment and tools
- Required business licenses and permits
- Insurance and legal setup costs
- Marketing and technology infrastructure
- Working capital and inventory

Please provide more details for a customized breakdown."""
async def generate_sales_projection_draft(business_context, current_question):
    """Generate dynamic, AI-powered sales projections for ANY business type"""
    industry = business_context.get("industry", "your industry")
    business_name = business_context.get("business_name", "your business")
    location = business_context.get("location", "your location")
    business_type = business_context.get("business_type", "service")
    
    prompt = f"""You are a business finance expert. Generate realistic first-year sales projections for "{business_name}" - a {industry} business in {location}.

CONTEXT:
- Industry: {industry}
- Business Type: {business_type}
- Location: {location}

Generate industry-specific sales projections using the CORRECT revenue model for {industry}:
- Service business: billable hours × hourly rate OR number of jobs × average price
- Product business: units sold × price per unit
- SaaS: monthly subscribers × price × 12 months
- Restaurant: covers per day × average check × days per year
- Retail: foot traffic × conversion rate × average purchase
- Consulting: billable hours × hourly rate × utilization rate

REQUIREMENTS:
1. Use industry-standard pricing for {industry} in {location}
2. Provide detailed calculation breakdown with correct math
3. Show weekly/monthly/annual projections
4. Include growth assumptions
5. Add critical considerations for {industry}
6. Format with clear sections and calculations

Be SPECIFIC to {industry} - use correct metrics, pricing, and volume assumptions for that industry."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating sales projections: {e}")
        return f"""Based on your {industry} business goals, create realistic first-year sales projections considering:
- Industry-standard pricing for {industry}
- Market size and accessibility in {location}
- Customer acquisition rate and conversion
- Seasonal variations
- Growth trajectory"""

async def generate_monthly_expenses_draft(business_context, current_question):
    """Generate dynamic, AI-powered monthly expenses for ANY business type"""
    industry = business_context.get("industry", "your industry")
    business_name = business_context.get("business_name", "your business")
    location = business_context.get("location", "your location")
    business_type = business_context.get("business_type", "service")
    
    prompt = f"""You are a business finance expert. Generate realistic monthly operating expenses for "{business_name}" - a {industry} business in {location}.

CONTEXT:
- Industry: {industry}
- Business Type: {business_type}
- Location: {location}

REQUIREMENTS:
1. Include industry-specific expense categories for {industry}
2. Automatically adjust ALL costs for {location}'s cost of living (research typical costs for that area)
3. Include ALL necessary expenses (don't miss vehicle costs if needed, rent if needed, etc.)
4. Provide realistic cost ranges (min - max)
5. Add helpful notes for each line item
6. Calculate total monthly expenses
7. Format as a table

For {industry} businesses, typical expense categories might include:
- Staffing (wages appropriate for {location})
- Facilities/rent (if needed for {industry})
- Vehicle costs (if {industry} requires transportation)
- Equipment/tools maintenance
- Materials/inventory
- Marketing & advertising
- Insurance & licenses
- Technology/software
- Utilities

**Total Monthly Expenses: $X,XXX - $X,XXX**

Adjust ALL numbers for {location}. Be SPECIFIC to {industry}."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1200
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating monthly expenses: {e}")
        return f"""Based on your {industry} business in {location}, consider these monthly expense categories:
- Staffing costs
- Facility/rent (if applicable)
- Vehicle/transportation (if applicable)
- Materials/inventory
- Marketing & advertising
- Insurance & licenses
- Technology & software"""
async def generate_customer_acquisition_cost_draft(business_context, current_question):
    """Generate dynamic, AI-powered CAC analysis for ANY business type"""
    industry = business_context.get("industry", "your industry")
    business_name = business_context.get("business_name", "your business")
    location = business_context.get("location", "your location")
    business_type = business_context.get("business_type", "service")
    
    prompt = f"""You are a business marketing expert. Generate a comprehensive Customer Acquisition Cost (CAC) analysis for "{business_name}" - a {industry} business in {location}.

CONTEXT:
- Industry: {industry}
- Business Type: {business_type}
- Location: {location}

REQUIREMENTS:
1. Identify industry-appropriate marketing channels for {industry} (NOT generic)
2. Use realistic costs for {location}'s market
3. Provide detailed CAC breakdown by channel
4. Calculate profitability (LTV:CAC ratio)
5. Give optimization recommendations
6. Format as tables

Marketing channels should be SPECIFIC to {industry}:
- B2B SaaS: LinkedIn Ads, content marketing, cold outreach, webinars
- Restaurant: Local SEO, food delivery apps, Instagram, Yelp
- E-commerce: Facebook/Instagram ads, Google Shopping, influencers
- Consulting: LinkedIn, referrals, speaking engagements, thought leadership
- Retail: Local ads, social media, events, partnerships
- Professional services: Referrals, networking, SEO, professional directories

Include:
- Monthly cost per channel
- Leads generated
- Conversion rates (industry-realistic)
- CAC per channel
- Total CAC
- LTV calculation
- LTV:CAC ratio
- Profitability assessment
- Optimization recommendations

Be SPECIFIC to {industry} - use actual channels that industry uses, not generic ones."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating CAC analysis: {e}")
        return f"""Customer Acquisition Cost Analysis for {industry} business:

Consider industry-appropriate channels for {industry}:
- Research which channels work best for {industry}
- Calculate realistic costs for {location}
- Determine conversion rates
- Calculate LTV:CAC ratio
- Assess profitability"""
