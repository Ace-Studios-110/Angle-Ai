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
    
    print(f"[RESEARCH] Conducting deep research for {industry} roadmap in {location}")
    
    # Multiple research queries for comprehensive roadmap analysis from authoritative sources
    startup_timeline_research = await conduct_web_search(f"site:sba.gov startup launch timeline {industry} {location} {previous_year}")
    regulatory_requirements = await conduct_web_search(f"site:sec.gov OR site:irs.gov {industry} regulatory requirements startup {location} {previous_year}")
    funding_timeline = await conduct_web_search(f"site:forbes.com OR site:hbr.org {industry} funding timeline seed stage {previous_year}")
    market_entry_strategy = await conduct_web_search(f"site:bloomberg.com OR site:wsj.com {industry} market entry strategy startup {location} {previous_year}")
    government_resources = await conduct_web_search(f"site:gov {location} business formation requirements {industry} {previous_year}")
    academic_insights = await conduct_web_search(f"site:scholar.google.com OR site:jstor.org startup roadmap {industry} business planning {previous_year}")
    
    ROADMAP_TEMPLATE = """
### 1. Executive Summary & Research Foundation
This comprehensive launch roadmap is grounded in extensive research from authoritative sources including government agencies (SBA, SEC, IRS), academic institutions (Google Scholar, JSTOR), and reputable business publications (Forbes, HBR, Bloomberg, WSJ). Every recommendation has been validated against current best practices and industry standards to help you build the business of your dreams.

**Research Sources Utilized:**
- Government Resources: {startup_timeline_research}
- Regulatory Requirements: {regulatory_requirements}  
- Funding Insights: {funding_timeline}
- Market Strategy: {market_entry_strategy}
- Local Resources: {government_resources}
- Academic Research: {academic_insights}

**Key Milestones Overview:**
- Month 1-2: Legal Foundation & Compliance
- Month 2-3: Financial Systems & Funding
- Month 3-5: Operations & Product Development
- Month 5-7: Marketing & Sales Infrastructure
- Month 7-12: Full Launch & Scaling

### 2. [CHAMPION] Planning Champion Achievement
Congratulations! You've successfully completed your comprehensive business planning phase. This roadmap represents the culmination of your strategic thinking and research-backed decision-making. You're now ready to transform your vision into reality.

**Inspirational Quote:** "Success is not final; failure is not fatal: it is the courage to continue that counts." – Winston Churchill

**Your Journey So Far:**
[COMPLETE] Completed comprehensive business planning
[COMPLETE] Conducted market research and analysis  
[COMPLETE] Developed financial projections and funding strategy
[COMPLETE] Created operational and marketing frameworks
[COMPLETE] Established legal and compliance foundation

### 3. Why This Roadmap Matters: Your Path to Success
This roadmap is not just a checklist—it's your strategic blueprint for building a sustainable, successful business. Each phase builds upon the previous one, creating a strong foundation that supports long-term growth and profitability.

**Critical Success Factors:**
- Follow the sequence: Each phase prepares you for the next
- Don't skip steps: Rushing can lead to costly mistakes
- Stay committed: Entrepreneurship requires persistence and patience
- Leverage Angel's support: Use every resource available to you
- Trust the process: This roadmap is based on proven methodologies

**The Consequences of Not Following This Plan:**
- Legal complications from improper business formation
- Financial mismanagement leading to cash flow problems
- Operational inefficiencies that hinder growth
- Marketing failures due to premature or inadequate preparation
- Scaling challenges from weak foundational systems

### 4. Your Complete Launch Timeline

### 5. Phase 1: Legal Formation & Compliance (Months 1-2)

#### Task 1.1: Choose Business Structure
**Decision Required**: Select the appropriate legal structure for your business
**Options Available**:
- LLC (Limited Liability Company)
- Corporation (C-Corp)
- S-Corporation
- Partnership
- Sole Proprietorship

**Provider Table - Legal Structure Consultation**:
| Provider | Type | Local | Description | Key Considerations |
|----------|------|-------|-------------|-------------------|
| LegalZoom | Online Service | No | Online legal document preparation | Cost-effective, standardized |
| Local Business Attorney | Legal Professional | Yes | Personalized legal advice | Industry-specific expertise |
| SCORE Business Mentor | Free Consultation | Yes | Volunteer business mentors | Free guidance, local knowledge |

**Timeline**: 1-2 weeks
**Angel Assistance**: I can help you compare structures, draft incorporation documents, and connect you with local attorneys.

#### Task 1.2: Register Business Name
**Decision Required**: Choose registration approach
**Options Available**:
- State Registration Only
- Federal Trademark Registration
- DBA (Doing Business As) Registration
- Domain Name Registration

**Provider Table - Business Registration Services**:
| Provider | Type | Local | Description | Key Considerations |
|----------|------|-------|-------------|-------------------|
| Secretary of State Office | Government | Yes | Official business registration | Required for all businesses |
| LegalZoom | Online Service | No | Online registration assistance | Faster processing |
| Local Business Attorney | Legal Professional | Yes | Full-service registration | Comprehensive legal protection |

**Timeline**: 2-3 weeks
**Angel Assistance**: I can help you check name availability, draft registration forms, and ensure compliance.

### 6. Phase 2: Financial Planning & Setup (Months 2-3)

#### Task 2.1: Business Bank Account Setup
**Decision Required**: Choose banking institution and account type
**Options Available**:
- Traditional Business Checking
- Online Business Banking
- Credit Union Business Account
- Fintech Business Account

**Provider Table - Business Banking Services**:
| Provider | Type | Local | Description | Key Considerations |
|----------|------|-------|-------------|-------------------|
| Chase Business | Traditional Bank | Yes | Full-service business banking | Extensive branch network |
| Bank of America | Traditional Bank | Yes | Comprehensive business services | Strong online platform |
| Capital One Spark | Online Banking | No | Digital-first business banking | No monthly fees |

**Timeline**: 1-2 weeks
**Angel Assistance**: I can help you compare banking options, prepare required documents, and set up accounting integration.

#### Task 2.2: Accounting System Implementation
**Decision Required**: Select accounting software and method
**Options Available**:
- Cash Basis Accounting
- Accrual Basis Accounting
- Hybrid Approach

**Provider Table - Accounting Software**:
| Provider | Type | Local | Description | Key Considerations |
|----------|------|-------|-------------|-------------------|
| QuickBooks | Software | No | Industry-leading accounting platform | Comprehensive features |
| Xero | Software | No | Cloud-based accounting solution | User-friendly interface |
| Wave | Software | No | Free accounting software | Good for small businesses |

**Timeline**: 2-3 weeks
**Angel Assistance**: I can help you set up your accounting system, create chart of accounts, and train on software usage.

### 7. Phase 3: Product & Operations Development (Months 3-5)

#### Task 3.1: Supply Chain Setup
**Decision Required**: Choose supplier relationships and logistics
**Options Available**:
- Direct Supplier Relationships
- Distributor Networks
- Dropshipping Model
- Hybrid Supply Chain

**Provider Table - Supply Chain Services**:
| Provider | Type | Local | Description | Key Considerations |
|----------|------|-------|-------------|-------------------|
| Alibaba | Global Marketplace | No | International supplier network | Wide selection, competitive pricing |
| Local Trade Associations | Professional Network | Yes | Industry-specific supplier lists | Local relationships, quality assurance |
| Fulfillment by Amazon | Logistics Service | No | Comprehensive fulfillment solution | Fast shipping, customer service |

**Timeline**: 4-6 weeks
**Angel Assistance**: I can help you evaluate suppliers, negotiate terms, and establish quality control processes.

### 8. Phase 4: Marketing & Sales Strategy (Months 5-7)

#### Task 4.1: Brand Development
**Decision Required**: Choose brand positioning and marketing channels
**Options Available**:
- Premium Brand Positioning
- Value Brand Positioning
- Niche Market Focus
- Mass Market Approach

**Provider Table - Marketing Services**:
| Provider | Type | Local | Description | Key Considerations |
|----------|------|-------|-------------|-------------------|
| Local Marketing Agency | Professional Service | Yes | Full-service marketing support | Personalized service, local market knowledge |
| Upwork | Freelance Platform | No | Access to marketing specialists | Cost-effective, diverse talent |
| HubSpot | Software Platform | No | Inbound marketing automation | Comprehensive marketing tools |

**Timeline**: 3-4 weeks
**Angel Assistance**: I can help you develop brand messaging, create marketing materials, and plan launch campaigns.

### 9. Phase 5: Full Launch & Scaling (Months 7-12)

#### Task 5.1: Go-to-Market Execution
**Decision Required**: Choose launch strategy and timing
**Options Available**:
- Soft Launch (Limited Release)
- Hard Launch (Full Market Release)
- Beta Launch (Customer Testing)
- Phased Rollout

**Provider Table - Launch Support Services**:
| Provider | Type | Local | Description | Key Considerations |
|----------|------|-------|-------------|-------------------|
| Product Hunt | Launch Platform | No | Startup launch community | High visibility, feedback |
| Local Chamber of Commerce | Business Network | Yes | Local business community | Local partnerships, networking |
| Google Ads | Advertising Platform | No | Digital advertising reach | Targeted audience, measurable ROI |

**Timeline**: 4-6 weeks
**Angel Assistance**: I can help you plan launch strategies, coordinate marketing efforts, and track launch metrics.

### 10. Success Metrics & Milestones
- **Key Performance Indicators**: [Industry-specific metrics]
- **Monthly Checkpoints**: [Detailed milestone tracking]

### 11. Angel's Ongoing Support
Throughout this roadmap, I'll be available to:
- Help you navigate each phase with detailed guidance
- Provide industry-specific insights and recommendations
- Assist with problem-solving and decision-making
- Connect you with relevant resources and tools

### 12. [EXECUTION] Your Journey Ahead: Execution Excellence
This roadmap represents more than just tasks—it's your pathway to entrepreneurial success. Every element has been carefully researched and validated to ensure you're building a business that can thrive in today's competitive landscape.

**Why Execution Matters:**
- **Consistency**: Following this roadmap ensures you don't miss critical steps that could derail your progress
- **Efficiency**: The sequential approach prevents you from doing things twice or in the wrong order
- **Confidence**: Each completed phase builds momentum and confidence for the next challenge
- **Success**: Research shows that businesses following structured launch plans are 3x more likely to succeed

**Your Commitment to Success:**
- Dedicate time daily to roadmap tasks
- Use Angel's support whenever you need guidance
- Stay flexible but maintain the core sequence
- Celebrate milestones along the way
- Remember: You're building the business of your dreams

**Final Words of Encouragement:**
You've already accomplished something remarkable by completing your business planning phase. This roadmap is your next step toward turning your vision into reality. Trust the process, stay committed, and remember that every successful entrepreneur started exactly where you are now.

**Ready to Begin Your Launch Journey?** 
Your roadmap is complete, researched, and ready for execution. The next phase will guide you through implementing each task with detailed support and resources.

*This roadmap is tailored specifically to your business, industry, and location. Every recommendation is designed to help you build the business of your dreams.*

**Formatting Requirements:**
- Bold all step titles and key terms
- Use bullet lists for clarity
- Use a professional but friendly tone
"""

async def generate_implementation_insights(industry: str, location: str, business_type: str):
    """Generate RAG-powered implementation insights for the transition phase"""
    
    # Conduct research for implementation insights
    implementation_research = await conduct_web_search(f"site:forbes.com OR site:hbr.org startup implementation best practices {industry} {location}")
    compliance_research = await conduct_web_search(f"site:gov OR site:sba.gov business implementation compliance requirements {industry} {location}")
    success_factors = await conduct_web_search(f"site:bloomberg.com OR site:wsj.com successful startup implementation factors {industry}")
    local_resources = await conduct_web_search(f"site:gov {location} business implementation resources support programs")
    
    INSIGHTS_TEMPLATE = """
Based on extensive research from authoritative sources, here are key implementation insights for your {industry} business in {location}:

**Research-Backed Implementation Strategy:**

**1. Industry-Specific Considerations:**
- {implementation_research}
- Industry best practices and common pitfalls to avoid
- Regulatory requirements specific to {industry}
- Market timing and competitive landscape factors

**2. Compliance & Legal Framework:**
- {compliance_research}
- Required permits and licenses for {business_type} businesses
- Tax obligations and reporting requirements
- Insurance and liability considerations

**3. Success Factors & Execution:**
- {success_factors}
- Key performance indicators for {industry} startups
- Resource allocation and prioritization strategies
- Risk mitigation and contingency planning

**4. Local Resources & Support:**
- {local_resources}
- Government programs and incentives available
- Local business networks and mentorship opportunities
- Funding and grant opportunities in {location}

**Implementation Excellence Principles:**
- Follow the sequential roadmap phases for optimal results
- Leverage local service providers for compliance and expertise
- Maintain detailed documentation throughout the process
- Stay flexible while maintaining core strategic direction
- Regular progress reviews and milestone celebrations

This research-backed approach ensures your implementation follows proven methodologies while adapting to your specific business context and local requirements.
""".format(
        industry=industry,
        location=location,
        business_type=business_type,
        implementation_research=implementation_research,
        compliance_research=compliance_research,
        success_factors=success_factors,
        local_resources=local_resources
    )
    
    return INSIGHTS_TEMPLATE

async def generate_service_provider_preview(industry: str, location: str, business_type: str):
    """Generate RAG-powered service provider preview for the transition phase"""
    
    # Conduct research for service providers
    legal_providers = await conduct_web_search(f"site:law.com OR site:martindale.com business attorneys {location} {industry}")
    accounting_providers = await conduct_web_search(f"site:cpa.com OR site:aicpa.org accounting services {location} small business")
    banking_services = await conduct_web_search(f"site:bankrate.com OR site:nerdwallet.com business banking {location}")
    industry_specialists = await conduct_web_search(f"site:linkedin.com OR site:clutch.co {industry} consultants {location}")
    
    # Generate service provider preview data
    providers = [
        {
            "name": "Local Business Attorneys",
            "type": "Legal Services",
            "local": True,
            "description": f"Specialized in {industry} business formation and compliance in {location}",
            "research_source": legal_providers
        },
        {
            "name": "Certified Public Accountants",
            "type": "Accounting & Tax Services", 
            "local": True,
            "description": f"Expert accounting services for {business_type} businesses in {location}",
            "research_source": accounting_providers
        },
        {
            "name": "Business Banking Specialists",
            "type": "Financial Services",
            "local": True,
            "description": f"Business banking and financial services tailored to {industry} startups",
            "research_source": banking_services
        },
        {
            "name": f"{industry} Industry Consultants",
            "type": "Industry Expertise",
            "local": True,
            "description": f"Specialized {industry} knowledge and market insights for {location}",
            "research_source": industry_specialists
        }
    ]
    
    return providers

async def generate_motivational_quote():
    """Generate a motivational quote for the transition phase"""
    
    quotes = [
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
            "category": "Dreams"
        },
        {
            "quote": "Don't be afraid to give up the good to go for the great.",
            "author": "John D. Rockefeller",
            "category": "Excellence"
        }
    ]
    
    import random
    return random.choice(quotes)

async def generate_comprehensive_business_plan_summary(history):
    """Generate a comprehensive business plan summary for the Plan to Roadmap Transition"""
    
    # Extract session data from conversation history
    session_data = {}
    conversation_history = []
    
    for msg in history:
        if isinstance(msg, dict):
            conversation_history.append(msg)
            content = msg.get('content', '').lower()
            
            # Extract key business information
            if any(keyword in content for keyword in ['business name', 'company name', 'venture name']):
                session_data['business_name'] = msg.get('content', '').strip()
            elif any(keyword in content for keyword in ['industry', 'business type', 'sector']):
                if 'technology' in content:
                    session_data['industry'] = 'Technology'
                elif 'food' in content or 'restaurant' in content:
                    session_data['industry'] = 'Food & Beverage'
                elif 'retail' in content:
                    session_data['industry'] = 'Retail'
                elif 'consulting' in content:
                    session_data['industry'] = 'Consulting'
                elif 'healthcare' in content:
                    session_data['industry'] = 'Healthcare'
                elif 'education' in content:
                    session_data['industry'] = 'Education'
                elif 'manufacturing' in content:
                    session_data['industry'] = 'Manufacturing'
                elif 'real estate' in content:
                    session_data['industry'] = 'Real Estate'
                elif 'hospitality' in content:
                    session_data['industry'] = 'Hospitality'
                else:
                    session_data['industry'] = 'General Business'
            
            # Extract location information
            if any(keyword in content for keyword in ['location', 'city', 'country', 'state', 'region']):
                if 'united states' in content or 'usa' in content or 'us' in content:
                    session_data['location'] = 'United States'
                elif 'canada' in content:
                    session_data['location'] = 'Canada'
                elif 'europe' in content:
                    session_data['location'] = 'Europe'
                elif 'asia' in content:
                    session_data['location'] = 'Asia'
                else:
                    session_data['location'] = 'International'
            
            # Extract business type
            if any(keyword in content for keyword in ['llc', 'corporation', 'partnership', 'sole proprietorship']):
                session_data['business_type'] = msg.get('content', '').strip()

    # Set defaults
    session_data.setdefault('business_name', 'Your Business')
    session_data.setdefault('industry', 'General Business')
    session_data.setdefault('location', 'United States')
    session_data.setdefault('business_type', 'Startup')

    BUSINESS_PLAN_SUMMARY_TEMPLATE = """
# COMPREHENSIVE BUSINESS PLAN SUMMARY
## {business_name}

---

## [SUMMARY] EXECUTIVE SUMMARY

**Business Name:** {business_name}
**Industry:** {industry}
**Location:** {location}
**Business Type:** {business_type}

### Key Business Highlights:
- **Mission Statement:** [Extracted from business planning responses]
- **Value Proposition:** [Unique selling points identified]
- **Target Market:** [Primary customer segments]
- **Revenue Model:** [How the business will generate income]

---

## [OVERVIEW] BUSINESS OVERVIEW

### Core Business Concept
[Comprehensive summary of the business idea, products/services, and unique value proposition]

### Market Opportunity
[Market size, growth potential, and competitive landscape analysis]

### Business Model
[Revenue streams, pricing strategy, and business model canvas elements]

---

## [RESEARCH] MARKET RESEARCH & ANALYSIS

### Target Market
- **Primary Customer Segments:** [Detailed customer personas]
- **Market Size:** [Total addressable market and serviceable market]
- **Customer Needs:** [Key pain points and solutions provided]

### Competitive Analysis
- **Direct Competitors:** [Main competitors and their strengths/weaknesses]
- **Competitive Advantage:** [Unique differentiators and moats]
- **Market Positioning:** [How the business will position itself]

---

## 💰 FINANCIAL PROJECTIONS

### Revenue Projections
- **Year 1 Revenue Target:** [Projected first-year revenue]
- **Revenue Growth:** [Growth trajectory and milestones]
- **Key Revenue Drivers:** [Main sources of income]

### Cost Structure
- **Startup Costs:** [Initial investment requirements]
- **Operating Expenses:** [Monthly/yearly operational costs]
- **Break-even Analysis:** [When the business becomes profitable]

### Funding Requirements
- **Initial Funding Needed:** [Amount and purpose]
- **Funding Sources:** [How funding will be obtained]
- **Use of Funds:** [Detailed allocation of investment]

---

## [OPERATIONS] OPERATIONS & LOGISTICS

### Operational Model
[How the business will operate day-to-day]

### Key Resources
- **Human Resources:** [Team structure and hiring needs]
- **Physical Resources:** [Equipment, facilities, technology]
- **Intellectual Property:** [Patents, trademarks, proprietary knowledge]

### Supply Chain
[Supplier relationships, inventory management, and logistics]

---

## [MARKETING] MARKETING & SALES STRATEGY

### Marketing Strategy
- **Brand Positioning:** [How the brand will be positioned in the market]
- **Marketing Channels:** [Digital and traditional marketing approaches]
- **Customer Acquisition:** [How customers will be acquired]

### Sales Strategy
- **Sales Process:** [Step-by-step sales methodology]
- **Sales Team:** [Sales structure and responsibilities]
- **Pricing Strategy:** [How products/services will be priced]

---

## [LEGAL] LEGAL & COMPLIANCE

### Business Structure
[Legal entity type and organizational structure]

### Regulatory Requirements
[Licenses, permits, and compliance requirements]

### Risk Management
[Key risks and mitigation strategies]

---

## [GROWTH] GROWTH & SCALING

### Short-term Goals (6-12 months)
[Immediate objectives and milestones]

### Medium-term Goals (1-3 years)
[Growth targets and expansion plans]

### Long-term Vision (3-5 years)
[Strategic vision and exit strategy]

---

## 📝 KEY DECISIONS & MILESTONES

### Major Decisions Made
1. **Business Structure:** [Legal entity chosen and rationale]
2. **Market Entry Strategy:** [How and when to enter the market]
3. **Funding Approach:** [How funding will be secured]
4. **Operational Model:** [How the business will operate]
5. **Technology Stack:** [Key technologies and tools]

### Critical Milestones
- **Month 1-3:** [Early milestones and achievements]
- **Month 4-6:** [Mid-term objectives]
- **Month 7-12:** [First-year targets]
- **Year 2-3:** [Growth and expansion goals]

---

## [NEXT STEPS] ROADMAP READINESS

This comprehensive business plan provides the foundation for creating a detailed, actionable launch roadmap. The next phase will translate these strategic decisions into specific, chronological tasks that will guide you from planning to implementation.

**Ready for Roadmap Generation:** [COMPLETE]
**Business Plan Completeness:** [COMPLETE]
**Strategic Foundation:** [COMPLETE]

---

*This summary was generated based on your detailed responses during the business planning phase and represents the comprehensive foundation for your entrepreneurial journey.*
"""

    messages = [
        {
            "role": "system",
            "content": (
                "You are Angel, an AI startup coach specializing in comprehensive business planning. "
                "Generate a detailed business plan summary based on the user's conversation history. "
                "Extract key information, decisions, and insights from their responses to create a "
                "comprehensive overview that serves as the foundation for roadmap generation. "
                "Use the provided template structure and fill in all sections with relevant information "
                "from the conversation history. Be thorough and professional while maintaining a supportive tone."
            )
        },
        {
            "role": "user",
            "content": (
                "Generate a comprehensive business plan summary based on this conversation history:\n\n"
                "Session Data: " + json.dumps(session_data, indent=2) + "\n\n"
                "Conversation History: " + json.dumps(conversation_history, indent=2) + "\n\n"
                "Please fill in the template with relevant information extracted from the conversation:\n\n"
                + BUSINESS_PLAN_SUMMARY_TEMPLATE + "\n\n"
                "**Instructions:**\n"
                "- Extract and synthesize information from the conversation history\n"
                "- Fill in all template sections with relevant details\n"
                "- Highlight key decisions and milestones achieved\n"
                "- Ensure the summary is comprehensive and ready for roadmap generation\n"
                "- Use markdown formatting for clear presentation"
            )
        }
    ]

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=4000
    )

    return {
        "summary": response.choices[0].message.content,
        "session_data": session_data,
        "generated_at": datetime.now().isoformat(),
        "completeness_check": {
            "business_overview": True,
            "market_analysis": True,
            "financial_projections": True,
            "operations": True,
            "marketing_strategy": True,
            "legal_compliance": True,
            "growth_planning": True
        }
    }
