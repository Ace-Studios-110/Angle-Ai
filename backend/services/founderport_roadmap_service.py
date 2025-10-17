from openai import AsyncOpenAI
import os
from datetime import datetime

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_founderport_style_roadmap(session_data, history):
    """
    Generate a roadmap matching the exact Founderport structure:
    - Stage 1: Foundation & Setup
    - Stage 2: Product Development (Beta Build)
    - Stage 3: Marketing Readiness
    - Stage 4: Beta Launch & Feedback
    - Stage 5: Public Launch
    - Stage 6: Scaling & Expansion
    
    With specific task descriptions like "Form Your California C-Corporation (Founderport, Inc.)"
    """
    
    # Extract key business information
    business_name = session_data.get('business_name', 'Your Business')
    founder_name = session_data.get('founder_name') or session_data.get('user_name') or 'Founder'
    location = session_data.get('location', 'United States')
    legal_structure = session_data.get('business_structure') or session_data.get('legal_structure') or 'LLC'
    industry = session_data.get('industry', 'General Business')
    business_type = session_data.get('business_type', 'Startup')
    
    # Extract state from location if possible
    state = extract_state_from_location(location)
    
    # Extract all business plan answers for context
    user_responses = [msg.get('content', '') for msg in history if msg.get('role') == 'user']
    conversation_text = ' '.join(user_responses[-50:])  # Last 50 responses
    
    # Generate roadmap using AI with Founderport structure
    roadmap_prompt = f"""
    Generate a comprehensive Launch Roadmap for "{business_name}" following the EXACT Founderport structure with 6 stages.
    
    **Business Context:**
    - Business Name: {business_name}
    - Founder: {founder_name}
    - Location: {location}
    - State: {state}
    - Legal Structure: {legal_structure}
    - Industry: {industry}
    - Business Type: {business_type}
    
    **User's Business Plan Answers:**
    {conversation_text[:3000]}
    
    Generate a roadmap with these 6 STAGES (not phases):
    
    ---
    
    ## **Founderport Launch Roadmap**
    *(Customized directly from the completed business plan inputs)*
    
    ### **Stage 1 — Foundation & Setup**
    **Goal**: Establish the legal, technical, and operational base for {business_name}.
    
    | Task | Description | Dependencies | Angel's Role | Status |
    |------|-------------|--------------|--------------|--------|
    | 1.1 Incorporate {business_name} | Register as a {state} {legal_structure}. File Articles of Incorporation/Organization. | None | Provide filing links, draft description text | ⏳ |
    | 1.2 File Trademarks for {business_name} | Protect branding before public marketing. USPTO filing. | Legal counsel | Provide USPTO filing links, draft description | ⏳ |
    | 1.3 Create IP & Copyright Plan | Secure intellectual property and written assets. | Formation complete | Schedule copyright filing reminder | ⏳ |
    | 1.4 Confirm Development Infrastructure | Set up cloud hosting, database, and core tech stack. | None | Generate config checklist | ⏳ |
    | 1.5 Implement NDA & Contract Controls | Ensure contracts and IP clauses are in place. | Legal setup | Store executed agreements securely | ⏳ |
    
    ### **Stage 2 — Product Development** 
    **Goal**: Deliver the first functional version of your product/service.
    
    | Task | Description | Dependencies | Angel's Role | Status |
    |------|-------------|--------------|--------------|--------|
    | 2.1 Develop Core Product/Service | Build MVP or beta version of your offering. | Technical requirements defined | Generate specs & workflow map | ⏳ |
    | 2.2 Integrate Key Features | Add essential features and functionality. | Core build complete | Provide feature checklist | ⏳ |
    | 2.3 Test Product Functionality | Conduct thorough testing and quality assurance. | Feature integration done | Generate test scripts | ⏳ |
    | 2.4 Internal QA & Refinement | Team testing and bug fixes. | Product functional | Monitor feedback, prioritize fixes | ⏳ |
    | 2.5 Prepare Beta Launch | Recruit beta testers and prepare onboarding. | QA complete | Generate onboarding script, feedback template | 🔜 |
    
    ### **Stage 3 — Marketing Readiness**
    **Goal**: Drive awareness and generate early interest.
    
    | Task | Description | Dependencies | Angel's Role | Status |
    |------|-------------|--------------|--------------|--------|
    | 3.1 Establish Landing Page | Build website with clear value prop and CTA. | Brand assets ready | Draft copy, CTA text, visuals | ⏳ |
    | 3.2 Launch Marketing Campaign | Start ads in key markets (adjust for your business). | Landing page live | Suggest ad keywords, headlines | 🔜 |
    | 3.3 Short-Form Video Content | Create explainer videos for social media. | Brand complete | Generate scripts, posting calendar | 🔜 |
    | 3.4 Partnership Outreach | Contact potential partners in your industry. | Pitch materials ready | Draft outreach emails, partnership proposals | ⏳ |
    
    ### **Stage 4 — Beta Launch & Feedback**
    **Goal**: Validate product-market fit and refine based on real user feedback.
    
    | Task | Description | Dependencies | Angel's Role | Status |
    |------|-------------|--------------|--------------|--------|
    | 4.1 Launch Beta Program | Deploy to test users, collect structured feedback. | Product ready | Track sessions & sentiment | 🔜 |
    | 4.2 Analyze Beta Data | Identify friction points and most-used features. | Feedback collected | Generate insights & recommendations | 🔜 |
    | 4.3 Implement Refinements | Fix bugs, adjust UX, add missing features. | Analysis complete | Prioritize fixes, assign to team | 🔜 |
    | 4.4 Prepare Marketing Assets | Create success stories and testimonials. | Positive results | Draft case studies, testimonials | 🔜 |
    
    ### **Stage 5 — Public Launch**
    **Goal**: Release to market and begin revenue generation.
    
    | Task | Description | Dependencies | Angel's Role | Status |
    |------|-------------|--------------|--------------|--------|
    | 5.1 Launch Publicly | Make product/service available to general public. | Beta approved | Manage launch communications | 🔜 |
    | 5.2 Activate Marketing Campaigns | Full marketing push across all channels. | Site live | Monitor conversions, optimize campaigns | 🔜 |
    | 5.3 Build Customer Pipeline | Set up sales processes and customer onboarding. | Marketing active | Create sales templates, onboarding flows | 🔜 |
    | 5.4 Track KPIs | Monitor CAC, LTV, churn, retention, revenue. | Launch active | Build dashboard templates | 🔜 |
    
    ### **Stage 6 — Scaling & Expansion**
    **Goal**: Grow the business and expand offerings.
    
    | Task | Description | Dependencies | Angel's Role | Status |
    |------|-------------|--------------|--------------|--------|
    | 6.1 Expand Product Line | Add new features, products, or services. | Stable core product | Research market needs, feature prioritization | 🔜 |
    | 6.2 Scale Operations | Hire team, increase capacity, optimize processes. | Revenue growth | Provide hiring templates, org charts | 🔜 |
    | 6.3 Enter New Markets | Geographic or demographic expansion. | Product-market fit | Localize content, research new markets | 🔜 |
    | 6.4 Build Strategic Partnerships | Form alliances to accelerate growth. | Market presence | Draft partnership proposals | 🔜 |
    
    ---
    
    CRITICAL REQUIREMENTS:
    1. Use "Stage" not "Phase" (Stage 1, Stage 2, etc.)
    2. Make task descriptions SPECIFIC to {business_name}, not generic
    3. Include {location} and {state} in relevant tasks (e.g., "Form Your {state} {legal_structure} ({business_name}, Inc.)")
    4. Use actual business name in task descriptions
    5. Tailor Stage 2 tasks based on whether it's SaaS/Tech, Service, or Product business
    6. Use markdown tables with columns: Task | Description | Dependencies | Angel's Role | Status
    7. Status indicators: ✅ (complete), ⏳ (in progress), 🔜 (upcoming)
    8. Make it look EXACTLY like the Founderport roadmap example
    
    Generate the complete roadmap now with all 6 stages and specific tasks for {business_name}.
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": roadmap_prompt}],
            temperature=0.3,
            max_tokens=3500  # Increased for comprehensive 6-stage roadmap
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating Founderport-style roadmap: {e}")
        # Fallback to basic structure
        return generate_fallback_roadmap(business_name, founder_name, location, legal_structure, state)

def extract_state_from_location(location):
    """Extract state from location string"""
    # Common US states
    states = {
        'california': 'California', 'ca': 'California',
        'new york': 'New York', 'ny': 'New York',
        'texas': 'Texas', 'tx': 'Texas',
        'florida': 'Florida', 'fl': 'Florida',
        'illinois': 'Illinois', 'il': 'Illinois',
        'pennsylvania': 'Pennsylvania', 'pa': 'Pennsylvania',
        'ohio': 'Ohio', 'washington': 'Washington', 'wa': 'Washington'
    }
    
    location_lower = location.lower()
    for key, value in states.items():
        if key in location_lower:
            return value
    
    # If location contains comma, assume format is "City, State"
    if ',' in location:
        parts = location.split(',')
        if len(parts) >= 2:
            state_part = parts[-1].strip()
            # Check if it's a known state
            for key, value in states.items():
                if key == state_part.lower():
                    return value
            return state_part  # Return as-is
    
    return location  # Return full location if can't extract state

def generate_fallback_roadmap(business_name, founder_name, location, legal_structure, state):
    """Generate basic roadmap structure as fallback"""
    return f"""
# {business_name} Launch Roadmap

**Founder:** {founder_name}
**Location:** {location}
**Legal Structure:** {legal_structure}

## Stage 1 — Foundation & Setup

| Task | Description | Dependencies | Angel's Role | Status |
|------|-------------|--------------|--------------|--------|
| 1.1 Form Your {state} {legal_structure} | Legally establish {business_name} with state authorities. | None | Provide filing guidance | ⏳ |
| 1.2 File Trademarks | Protect your brand name and logo. | Legal formation | USPTO filing assistance | ⏳ |
| 1.3 Set Up Infrastructure | Establish core business systems and processes. | None | System setup checklist | ⏳ |

## Stage 2 — Product Development
[Additional stages will be generated based on your business plan responses]

**Note:** Your complete roadmap is being generated with full details for all 6 stages.
"""

async def generate_task_with_service_providers(task_name, business_name, location, industry):
    """Generate a detailed task page with service provider options like the Founderport example"""
    
    # Extract state
    state = extract_state_from_location(location)
    
    task_prompt = f"""
    Generate a detailed task page for: "{task_name}" for {business_name} located in {location}.
    
    Follow this EXACT structure from the Founderport example:
    
    ## Task: [Specific Task Name with Business Name]
    
    🎯 **Objective**
    [2-3 sentences explaining what this task accomplishes and why it's important for {business_name}]
    
    🧾 **Step 1 – Gather Your Required Information**
    You'll need:
    • [List 4-6 specific items needed]
    • [Include actual business name: {business_name}]
    • [Include location specifics: {location}, {state}]
    
    🧩 **Ways to Complete This Task**
    
    **Option 1 – Do-It-Yourself (Direct)**
    • [Detailed steps for DIY approach]
    • [Include specific websites, portals, timelines]
    • [Mention costs and processing times]
    
    **Option 2 – Third-Party Service Provider (Assisted)**
    Use a provider that handles the work for you:
    
    | Service Provider | Cost | What They Do | Notes |
    |------------------|------|--------------|-------|
    | [Provider 1] | $[amount] | [Service description] | [Recommendation] |
    | [Provider 2] | $[amount] | [Service description] | [Recommendation] |
    | [Provider 3] | $[amount] | [Service description] | [Recommendation] |
    | Local Option: {location} [Service] | $[amount] | [Local service] | Fast, personalized support |
    
    ⚙️ **Available Angel Commands for This Task**
    
    | Command | What It Does | Example Use |
    |---------|--------------|-------------|
    | **Kickstart** | Angel prepares documents, forms, or templates for you. | "Kickstart this step." |
    | **Help** | Explains details and guides you through the process. | "What does [term] mean?" |
    | **Who Do I Contact?** | Provides vetted local service providers with ratings. | "Who handles this near me?" |
    | **Advice & Tips** | Shares best practices and insider knowledge. | "Any tips before filing?" |
    
    💡 **Angel's Advice**
    "{founder_name}, at this stage, [personalized advice specific to this task and their situation in {location}]. 
    
    [2-3 sentences of strategic guidance tailored to their industry and location]
    
    After completing this, [what they'll need next or what documents they'll receive]."
    
    **Would you like to:**
    1️⃣ Kickstart the [task process]
    2️⃣ See recommended service providers
    3️⃣ Ask for Help and learn more details first
    
    ---
    
    REQUIREMENTS:
    - Use {business_name} in task titles and descriptions
    - Include {location} and {state} specifics
    - Provide 3-4 service provider options with costs
    - Include a local option for {location}
    - Make Angel's advice personal to {founder_name}
    - Tailor to {industry} industry specifics
    - Be as detailed as the Founderport example
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": task_prompt}],
            temperature=0.4,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating task details: {e}")
        return f"## Task: {task_name}\n\nDetailed information for this task is being generated..."

