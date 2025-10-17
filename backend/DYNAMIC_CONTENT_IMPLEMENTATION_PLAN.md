# Dynamic Content Implementation Plan

## CRITICAL: Current Implementation is NOT Fully Dynamic

### Problems Identified:

1. **Roadmap content uses generic templates** instead of business-specific tasks
2. **Business plan summary doesn't match Founderport example structure**
3. **Transition messages use placeholders** but don't pull all relevant session data
4. **Task descriptions are generic** instead of industry-specific

---

## Required Changes for Full Dynamic Implementation

### 1. Business Plan Summary Generation (MUST FIX)

**Current**: Generic summary
**Required**: Match Founderport structure exactly

**File**: `Angle-Ai/backend/services/angel_service.py` - `generate_business_plan_summary()`

**Required Structure**:
```python
async def generate_business_plan_summary(session_data, history):
    """
    Generate comprehensive business plan matching Founderport example structure:
    1. Business Overview (Mission, Vision)
    2. Product/Service Details
    3. Market Research
    4. Location & Operations
    5. Revenue Model & Financials
    6. Marketing & Sales Strategy
    7. Legal & Administrative
    8. Growth & Scaling
    9. Challenges & Contingency Planning
    """
    
    # Extract ALL business plan answers from history
    business_plan_data = extract_all_business_plan_answers(history)
    
    # Use AI to structure into Founderport format
    summary_prompt = f"""
    Generate a comprehensive business plan summary in this EXACT structure:
    
    **Business Name**: {session_data.get('business_name')}
    **Founder**: {session_data.get('founder_name') or 'Founder'}
    **Location**: {session_data.get('location')}
    **Legal Structure**: {session_data.get('business_structure')}
    
    1. Business Overview
       - Mission Statement
       - Vision Statement
    
    2. Product / Service Details
       - Core Offering
       - Key Features
       - Differentiation
    
    3. Market Research
       - Industry Context
       - Target Market
       - Competitive Landscape
       - Market Opportunity
    
    4. Location & Operations
       - Base location and operations structure
    
    5. Revenue Model & Financials
       - Primary revenue model
       - Supplementary streams
       - Startup costs
       - Financial outlook
    
    6. Marketing & Sales Strategy
       - Core channels
       - Sales funnel
       - Key messages
    
    7. Legal & Administrative
       - Entity type
       - Compliance requirements
       - IP strategy
    
    8. Growth & Scaling
       - Year 1-5 plan
    
    9. Challenges & Contingency Planning
       - Key risks and mitigation strategies
    
    Use this business plan data: {business_plan_data}
    """
    
    # Generate structured summary
    # Return formatted markdown
```

---

### 2. Dynamic Roadmap Generation (MUST FIX)

**Current**: Hardcoded generic tasks
**Required**: Business-type-specific tasks like Founderport example

**File**: `Angle-Ai/backend/services/generate_plan_service.py`

**Required Logic**:
```python
async def generate_dynamic_roadmap(session_data, history):
    """
    Generate roadmap with business-specific tasks
    """
    # Extract business context
    business_name = session_data.get('business_name')
    business_type = session_data.get('business_type')  # SaaS, Service, Product, etc.
    industry = session_data.get('industry')
    location = session_data.get('location')
    legal_structure = session_data.get('business_structure')
    
    # Determine roadmap template based on business type
    if is_saas_or_tech(business_type, industry):
        stages = [
            "Foundation & Setup",
            "Product Development (Beta Build)",
            "Marketing Readiness",
            "Beta Launch & Feedback",
            "Public Launch",
            "Scaling & Expansion"
        ]
        tasks = generate_saas_tasks(business_name, location, legal_structure)
    
    elif is_service_business(business_type, industry):
        stages = [
            "Legal Formation",
            "Financial Planning",
            "Licensing & Permits",
            "Marketing & Branding",
            "Operations Setup",
            "Launch & Growth"
        ]
        tasks = generate_service_tasks(business_name, location, legal_structure)
    
    elif is_product_business(business_type, industry):
        stages = [
            "Legal Formation",
            "Product Development",
            "Manufacturing & Supply Chain",
            "Marketing & Sales",
            "Launch & Distribution",
            "Scaling"
        ]
        tasks = generate_product_tasks(business_name, location, legal_structure)
    
    # Generate each task with:
    # - Task name
    # - Description (specific to their business)
    # - Dependencies
    # - Timeline
    # - Service providers (filtered by location)
    # - Research sources
```

---

### 3. Session Data Extraction (MUST BE COMPLETE)

**Current**: Basic extraction
**Required**: Extract ALL business plan answers

**File**: `Angle-Ai/backend/services/angel_service.py`

**Required Fields** (from Business Plan questions):
```python
session_data = {
    # KYC Data
    "business_name": "Founderport",
    "founder_name": "Kevin Moore",
    "location": "Santee, California",
    "industry": "Entrepreneurship Support / SaaS",
    "business_experience": "Experienced",
    
    # Business Plan Data
    "mission": "Founderport empowers entrepreneurs...",
    "vision": "To become the go-to digital launchpad...",
    "business_structure": "C-Corporation (California)",
    "target_market": "Novice entrepreneurs, tradespeople...",
    "value_proposition": "AI-powered end-to-end...",
    "competitive_advantage": "No existing platform offers...",
    "revenue_model": "Subscription ($20/mo or $200/yr)",
    "startup_costs": {...},
    "marketing_strategy": {...},
    "sales_strategy": {...},
    "operational_plan": {...},
    "financial_projections": {...},
    "legal_compliance": {...},
    "growth_plan": {...},
    "risk_mitigation": {...}
}
```

---

### 4. Transition Messages Must Use ALL Dynamic Data

**Current**: Uses some session data
**Required**: Use comprehensive personalization

**Example for KYC → Business Plan**:
```python
transition_message = f"""
🎉 CONGRATULATIONS! You've completed the Business Planning Phase!

**{session_data.get('founder_name', 'Founder')}, here's what we've captured:**

Business: {business_name}
Industry: {industry}
Location: {location}
Experience Level: {business_experience}

[Continue with full dynamic content...]
"""
```

---

### 5. Task Examples Must Be Business-Specific

**Current**: Generic "Register C-Corp"
**Required**: "Form Your California C-Corporation (Founderport, Inc.)" like in the document

**Example Task Template**:
```python
def generate_incorporation_task(business_name, location, legal_structure):
    state = extract_state(location)  # "California" from "Santee, California"
    
    return {
        "name": f"Form Your {state} {legal_structure} ({business_name})",
        "objective": f"Legally establish {business_name} with the {state} Secretary of State.",
        "steps": [
            f"Gather required information for {business_name}",
            f"Choose filing method (DIY vs. service provider)",
            f"File Articles of Incorporation in {state}",
            "Obtain confirmation and Entity Number"
        ],
        "service_providers": get_local_legal_services(location),
        "timeline": "1-2 weeks",
        "angel_commands": {
            "Kickstart": f"Prepare Articles of Incorporation for {business_name}",
            "Help": "Explain form fields and submission process",
            "Who Do I Contact?": f"Show vetted registered agents in {location}"
        }
    }
```

---

## Implementation Priority

### Phase 1: CRITICAL (Fix Now)
1. ✅ Fix `generate_business_plan_summary()` to match Founderport structure
2. ✅ Make roadmap generation fully dynamic based on business type
3. ✅ Ensure ALL session data is extracted and stored
4. ✅ Update transitions to use comprehensive session data

### Phase 2: IMPORTANT
1. Create business-type-specific task templates
2. Generate industry-specific service provider recommendations
3. Add location-based filtering for resources
4. Implement dependency tracking for tasks

### Phase 3: ENHANCEMENTS
1. Add real-time task progress tracking
2. Implement smart suggestions based on business type
3. Add competitor-specific research
4. Implement milestone celebrations

---

## Testing Checklist

### Dynamic Content Tests:
- [ ] Business plan summary matches Founderport structure
- [ ] All business name mentions are from session data
- [ ] All location mentions are from session data
- [ ] Legal structure is dynamically inserted
- [ ] Roadmap tasks are specific to business type
- [ ] Service providers are filtered by location
- [ ] No hardcoded names or locations appear
- [ ] Task descriptions reference actual business name
- [ ] Financial projections use user's numbers
- [ ] Marketing strategy reflects user's answers

---

## Example: Before vs. After

### BEFORE (Hardcoded):
```
Task: Register Your C-Corporation
Description: File with Secretary of State
Location: United States
```

### AFTER (Dynamic):
```
Task: Form Your California C-Corporation (Founderport, Inc.)
Description: Legally establish Founderport, Inc. with the California Secretary of State
Location: Santee, California
Registered Agent Options:
  - LegalZoom (National)
  - Clerky (Startup-focused)
  - Santee Legal Services (Local, $175-250)
```

---

## Conclusion

The current implementation has the **structure** correct, but the **content needs to be fully dynamic**. Every business name, location, legal structure, and task description must come from the user's session data and business plan answers, not from hardcoded templates.

This will make Founderport truly personalized for each entrepreneur, just like the example shows for Kevin Moore's business.

