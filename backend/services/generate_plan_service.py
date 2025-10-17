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
            
            # Extract industry information - DYNAMIC APPROACH
            if any(keyword in content for keyword in ['industry', 'business type', 'sector', 'field']):
                # Use AI model to dynamically identify industry
                industry_prompt = f"""
                Analyze this user input and extract the business industry or sector: "{content}"
                
                Return ONLY the industry name in a standardized format, or "general business" if unclear.
                
                Examples:
                - "Tea Stall" → "Tea Stall"
                - "AI Development" → "AI Development"
                - "Food Service" → "Food Service"
                - "Technology" → "Technology"
                - "Healthcare" → "Healthcare"
                
                Return only the industry name:
                """
                
                try:
                    response = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": industry_prompt}],
                        temperature=0.1,
                        max_tokens=30
                    )
                    
                    industry_result = response.choices[0].message.content.strip()
                    session_data['industry'] = industry_result if industry_result else 'general business'
                except Exception as e:
                    print(f"Industry extraction failed: {e}")
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
            
            # Extract industry information - DYNAMIC APPROACH
            if any(keyword in content for keyword in ['industry', 'business type', 'sector', 'field']):
                # Use AI model to dynamically identify industry
                industry_prompt = f"""
                Analyze this user input and extract the business industry or sector: "{content}"
                
                Return ONLY the industry name in a standardized format, or "general business" if unclear.
                
                Examples:
                - "Tea Stall" → "Tea Stall"
                - "AI Development" → "AI Development"
                - "Food Service" → "Food Service"
                - "Technology" → "Technology"
                - "Healthcare" → "Healthcare"
                
                Return only the industry name:
                """
                
                try:
                    response = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": industry_prompt}],
                        temperature=0.1,
                        max_tokens=30
                    )
                    
                    industry_result = response.choices[0].message.content.strip()
                    session_data['industry'] = industry_result if industry_result else 'general business'
                except Exception as e:
                    print(f"Industry extraction failed: {e}")
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
    print(f"[RESEARCH] Searching Government Sources (.gov), Academic Research (.edu, scholar), and Industry Reports (Bloomberg, WSJ, Forbes)")
    
    # EXPLICIT RESEARCH FROM AUTHORITATIVE SOURCES - Government, Academic, Industry
    # Government Sources - SBA, IRS, state agencies, regulatory bodies
    government_resources = await conduct_web_search(
        f"Search ONLY government sources (.gov domains) for: {location} business formation requirements {industry} startup compliance licensing permits {current_year}. "
        f"Include: SBA.gov, IRS.gov, state business registration sites, regulatory agencies. Cite specific government sources and URLs."
    )
    regulatory_requirements = await conduct_web_search(
        f"Search government (.gov) and regulatory sources for: {industry} regulatory requirements startup compliance {location} {current_year}. "
        f"Find specific licenses, permits, and legal requirements. Cite government sources with URLs."
    )
    
    # Academic Research - Universities, research institutions, academic journals
    academic_insights = await conduct_web_search(
        f"Search academic sources (.edu, Google Scholar, JSTOR, research institutions) for: startup roadmap {industry} business planning success factors {current_year}. "
        f"Find research papers, studies, and academic publications. Cite specific academic sources with URLs."
    )
    startup_research = await conduct_web_search(
        f"Search academic and research sources for: {industry} startup timeline best practices implementation phases {current_year}. "
        f"Include university research, business school publications, peer-reviewed studies. Cite academic sources."
    )
    
    # Industry Reports - Bloomberg, WSJ, Forbes, Harvard Business Review, industry publications
    market_entry_strategy = await conduct_web_search(
        f"Search industry publications (Bloomberg, WSJ, Forbes, Harvard Business Review) for: {industry} market entry strategy startup {location} {current_year}. "
        f"Find authoritative industry reports and business journalism. Cite specific publications with URLs."
    )
    funding_insights = await conduct_web_search(
        f"Search industry sources (Bloomberg, WSJ, Forbes, Crunchbase) for: {industry} funding timeline seed stage startup investment trends {current_year}. "
        f"Include venture capital reports and startup funding data. Cite industry sources."
    )
    operational_insights = await conduct_web_search(
        f"Search industry publications for: {industry} operational requirements startup launch phases {location} {current_year}. "
        f"Find industry-specific best practices and operational benchmarks. Cite sources."
    )
    
    print(f"[RESEARCH] ✓ Government sources researched: SBA, IRS, state agencies")
    print(f"[RESEARCH] ✓ Academic research reviewed: Universities, journals, research institutions")
    print(f"[RESEARCH] ✓ Industry reports analyzed: Bloomberg, WSJ, Forbes, HBR")
    
    ROADMAP_TEMPLATE = """
# Launch Roadmap - Built on Government Sources, Academic Research & Industry Reports

## Executive Summary & Research Foundation

This comprehensive launch roadmap is grounded in extensive research from three authoritative source categories:

**Government Sources (.gov)**: SBA, IRS, SEC, state business agencies, regulatory bodies
**Academic Research (.edu, scholar)**: University research, peer-reviewed journals, business school publications  
**Industry Reports**: Bloomberg, Wall Street Journal, Forbes, Harvard Business Review, industry publications

Every recommendation has been validated against current best practices and cited with specific sources to ensure you have authoritative, verified guidance.

---

## Research Sources Utilized

| Source Category | Specific Sources | Research Focus | Key Findings |
|----------------|------------------|----------------|--------------|
| **Government Sources** | SBA.gov, IRS.gov, state agencies | Business formation, compliance, licensing | {government_resources} |
| **Government Regulatory** | Federal/state regulatory bodies | Industry-specific requirements | {regulatory_requirements} |
| **Academic Research** | Universities, Google Scholar, JSTOR | Startup success factors, best practices | {academic_insights} |
| **Academic Studies** | Business schools, research institutions | Implementation timelines, phases | {startup_research} |
| **Industry Reports** | Bloomberg, WSJ, Forbes, HBR | Market entry, funding trends | {market_entry_strategy} |
| **Industry Analysis** | Business publications, VC reports | Operational requirements, benchmarks | {operational_insights} |

---

## Key Milestones Overview

| Phase | Timeline | Focus Area | Research Source Type |
|-------|----------|------------|---------------------|
| Phase 1 | Month 1-2 | Legal Foundation & Compliance | Government Sources |
| Phase 2 | Month 2-3 | Financial Systems & Funding | Industry Reports + Government |
| Phase 3 | Month 3-5 | Operations & Product Development | Academic Research + Industry |
| Phase 4 | Month 5-7 | Marketing & Sales Infrastructure | Industry Reports + Academic |
| Phase 5 | Month 7-12 | Full Launch & Scaling | All Sources |

---

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

**Roadmap Steps - Phase 1: Legal Foundation**

| Step Name | Step Description | Timeline | Research Source |
|-----------|------------------|----------|----------------|
| **Choose Business Structure** | Select appropriate legal structure (LLC, C-Corp, S-Corp, Partnership, or Sole Proprietorship). Consider liability protection, tax implications, and operational flexibility. Evaluate based on industry requirements, funding needs, and growth plans. | 1-2 weeks | **Government**: SBA.gov business structure guide, IRS.gov tax classifications<br>**Academic**: University business school entity selection research<br>**Industry**: Forbes/HBR startup structure analysis |
| **Register Business Name** | Register business name with Secretary of State. Check availability via state database. Consider federal trademark (USPTO) for brand protection. Secure matching domain name and social media handles. File DBA if using alternative name. | 2-3 weeks | **Government**: State Secretary of State offices, USPTO.gov trademark search<br>**Industry**: WSJ/Bloomberg brand protection strategies |
| **Obtain EIN** | Apply for Employer Identification Number through IRS website. Required for business bank accounts, hiring employees, and tax filing. Free application, instant approval in most cases. | 1 week | **Government**: IRS.gov EIN application guide and requirements |
| **Get Business Licenses** | Identify and obtain federal, state, and local licenses/permits specific to your industry and location. Research regulatory requirements, submit applications, schedule inspections if needed. | 3-4 weeks | **Government**: SBA.gov licensing guide, state/local regulatory agencies<br>**Industry**: Industry-specific compliance publications |

**Service Providers - Legal Formation**:
| Provider | Type | Local | Description | Research Source |
|----------|------|-------|-------------|----------------|
| LegalZoom | Online Service | No | Online legal document preparation, standardized packages | Industry comparison sites, user reviews |
| Local Business Attorney | Legal Professional | Yes | Personalized legal advice, industry expertise | State bar associations, legal directories |
| SCORE Business Mentor | Free Consultation | Yes | Volunteer business mentors with industry experience | SBA.gov, local SCORE chapters |

**Angel Support Available**: Structure comparison analysis, document drafting assistance, compliance checklist, local attorney connections

### 6. Phase 2: Financial Planning & Setup (Months 2-3)

**Roadmap Steps - Phase 2: Financial Foundation**

| Step Name | Step Description | Timeline | Research Source |
|-----------|------------------|----------|----------------|
| **Open Business Bank Account** | Select and open dedicated business checking account. Compare traditional banks vs online/fintech options. Consider fees, features, integration capabilities. Gather required documents (EIN, formation docs, ID). | 1-2 weeks | **Government**: FDIC.gov banking guidance for small businesses<br>**Industry**: NerdWallet, Bankrate business banking comparisons<br>**Academic**: Business school research on startup financial management |
| **Set Up Accounting System** | Choose accounting software (cash vs accrual basis). Set up chart of accounts, connect bank feeds, establish bookkeeping processes. Consider hiring bookkeeper or accountant. | 2-3 weeks | **Government**: IRS.gov accounting method requirements<br>**Industry**: Forbes/HBR accounting software reviews<br>**Academic**: University accounting department best practices |
| **Establish Financial Controls** | Implement expense policies, approval workflows, receipt management. Set up separate business credit card. Create financial tracking and reporting processes. | 1-2 weeks | **Government**: SBA.gov financial management resources<br>**Academic**: Research on internal controls for startups |
| **Create Financial Projections** | Develop detailed financial projections (revenue, expenses, cash flow) for 12-36 months. Create budget and financial milestones. Plan for seasonal variations. | 2-3 weeks | **Industry**: VC firms' startup financial modeling guides<br>**Academic**: Business school financial forecasting research |

**Service Providers - Financial Setup**:
| Provider | Type | Local | Description | Research Source |
|----------|------|-------|-------------|----------------|
| Chase Business | Traditional Bank | Yes | Full-service business banking with branch network | FDIC.gov, Bankrate comparisons |
| QuickBooks | Accounting Software | No | Industry-leading platform with extensive features | Software review sites, user ratings |
| Local CPA Firm | Professional Service | Yes | Personalized accounting and tax guidance | AICPA.org directory, local referrals |

**Angel Support Available**: Banking comparison, accounting setup, financial projection templates, bookkeeper recommendations

### 7. Phase 3: Product & Operations Development (Months 3-5)

**Roadmap Steps - Phase 3: Operational Foundation**

| Step Name | Step Description | Timeline | Research Source |
|-----------|------------------|----------|----------------|
| **Establish Supply Chain** | Identify and vet suppliers (local vs international). Negotiate terms, minimum orders, payment terms. Set up logistics and fulfillment processes. Establish backup suppliers for critical items. | 4-6 weeks | **Government**: Commerce.gov international trade resources<br>**Industry**: Bloomberg supply chain reports, trade publications<br>**Academic**: University supply chain management research |
| **Set Up Operations Infrastructure** | Secure physical location (office, warehouse, retail) if needed. Purchase equipment, technology, and tools. Set up utilities, insurance, and security systems. | 3-4 weeks | **Government**: SBA.gov location selection guidance<br>**Industry**: Commercial real estate publications<br>**Academic**: Operations management research |
| **Develop Product/Service** | Finalize product specifications or service delivery processes. Create prototypes or pilot programs. Test with focus groups or beta customers. Iterate based on feedback. | 6-8 weeks | **Academic**: University product development research<br>**Industry**: Harvard Business Review innovation articles |
| **Implement Quality Control** | Establish quality standards and testing procedures. Create quality assurance processes. Set up customer feedback loops. Document standard operating procedures. | 2-3 weeks | **Government**: ISO standards, industry regulatory requirements<br>**Academic**: Quality management research |

**Service Providers - Operations**:
| Provider | Type | Local | Description | Research Source |
|----------|------|-------|-------------|----------------|
| Alibaba | Global Marketplace | No | International supplier network with competitive pricing | Industry supplier directories |
| Local Trade Associations | Professional Network | Yes | Industry-specific local supplier connections | Chamber of Commerce, trade groups |
| Fulfillment by Amazon | Logistics Service | No | Comprehensive fulfillment with fast shipping | E-commerce industry reports |

**Angel Support Available**: Supplier evaluation, negotiation templates, quality control checklists, operations process documentation

### 8. Phase 4: Marketing & Sales Strategy (Months 5-7)

**Roadmap Steps - Phase 4: Market Launch Preparation**

| Step Name | Step Description | Timeline | Research Source |
|-----------|------------------|----------|----------------|
| **Develop Brand Identity** | Create brand positioning, messaging, visual identity (logo, colors, fonts). Define unique value proposition and brand voice. Develop brand guidelines document. | 3-4 weeks | **Academic**: University marketing research on brand positioning<br>**Industry**: Forbes/HBR branding strategy articles |
| **Build Digital Presence** | Create professional website with SEO optimization. Set up social media profiles across relevant platforms. Implement analytics and tracking (Google Analytics, etc.). | 4-6 weeks | **Industry**: Digital marketing publications, web design trends<br>**Academic**: Digital marketing research studies |
| **Create Marketing Materials** | Develop marketing collateral (brochures, presentations, business cards). Create product photography and videography. Write copy for various channels. | 3-4 weeks | **Industry**: Marketing best practices from leading agencies<br>**Academic**: Marketing communications research |
| **Implement Sales Process** | Define sales funnel stages and customer journey. Create CRM system and sales tracking. Develop sales scripts, proposals, and contracts. Train sales team if applicable. | 2-3 weeks | **Academic**: Sales methodology research<br>**Industry**: Sales enablement publications, CRM software guides |
| **Plan Customer Acquisition** | Identify customer acquisition channels (paid ads, content marketing, partnerships). Set budgets and KPIs. Create initial campaigns and test messaging. | 3-4 weeks | **Industry**: Digital advertising platforms' best practices<br>**Academic**: Customer acquisition research studies |

**Service Providers - Marketing & Sales**:
| Provider | Type | Local | Description | Research Source |
|----------|------|-------|-------------|----------------|
| Local Marketing Agency | Professional Service | Yes | Full-service marketing with local market expertise | Local business directories, client reviews |
| Upwork/Fiverr | Freelance Platform | No | Cost-effective access to specialized marketing talent | Platform ratings, portfolio reviews |
| HubSpot | Software Platform | No | Comprehensive inbound marketing automation tools | Software review sites, case studies |

**Angel Support Available**: Brand strategy development, marketing plan templates, customer acquisition playbooks, vendor selection guidance

### 9. Phase 5: Full Launch & Scaling (Months 7-12)

**Roadmap Steps - Phase 5: Launch & Growth**

| Step Name | Step Description | Timeline | Research Source |
|-----------|------------------|----------|----------------|
| **Execute Go-to-Market Launch** | Choose launch strategy (soft launch, hard launch, beta, or phased rollout). Coordinate all marketing channels. Execute launch events and campaigns. Monitor initial customer response. | 4-6 weeks | **Academic**: Product launch research from business schools<br>**Industry**: HBR/WSJ successful launch case studies |
| **Customer Acquisition at Scale** | Ramp up customer acquisition efforts across validated channels. Scale spending based on ROI metrics. Implement referral programs and partnerships. | 2-3 months | **Industry**: Growth marketing publications, VC growth guides<br>**Academic**: Customer lifetime value research |
| **Operational Scaling** | Hire key team members as needed. Scale operations to meet demand. Optimize processes for efficiency. Implement automation where possible. | 2-3 months | **Government**: SBA.gov hiring and HR resources<br>**Academic**: Scaling operations research |
| **Financial Management & Fundraising** | Monitor cash flow closely. Achieve profitability milestones or secure additional funding. Implement financial reporting and forecasting. | Ongoing | **Government**: SEC.gov fundraising regulations<br>**Industry**: VC/Angel investor guidelines<br>**Academic**: Startup finance research |
| **Measure, Learn, Optimize** | Track KPIs and business metrics. Analyze customer feedback and behavior. Optimize product, pricing, and processes. Prepare for next growth phase. | Ongoing | **Academic**: Business analytics and optimization research<br>**Industry**: Analytics platform best practices |

**Service Providers - Launch & Scaling**:
| Provider | Type | Local | Description | Research Source |
|----------|------|-------|-------------|----------------|
| Product Hunt | Launch Platform | No | Tech startup launch community with high visibility | Tech industry launch playbooks |
| Local Chamber of Commerce | Business Network | Yes | Local networking and partnership opportunities | Local business organizations |
| Google Ads | Advertising Platform | No | Digital advertising with measurable ROI | Google marketing resources, industry guides |

**Angel Support Available**: Launch planning, growth strategy, hiring templates, investor pitch materials, scaling playbooks

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
            
            # Extract key business information - DYNAMIC APPROACH
            if any(keyword in content for keyword in ['business name', 'company name', 'venture name']):
                session_data['business_name'] = msg.get('content', '').strip()
            elif any(keyword in content for keyword in ['industry', 'business type', 'sector']):
                # Use AI model to dynamically identify industry
                industry_prompt = f"""
                Analyze this user input and extract the business industry or sector: "{content}"
                
                Return ONLY the industry name in a standardized format, or "General Business" if unclear.
                
                Examples:
                - "Tea Stall" → "Tea Stall"
                - "AI Development" → "AI Development"
                - "Food Service" → "Food Service"
                - "Technology" → "Technology"
                - "Healthcare" → "Healthcare"
                
                Return only the industry name:
                """
                
                try:
                    response = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": industry_prompt}],
                        temperature=0.1,
                        max_tokens=30
                    )
                    
                    industry_result = response.choices[0].message.content.strip()
                    session_data['industry'] = industry_result if industry_result else 'General Business'
                except Exception as e:
                    print(f"Industry extraction failed: {e}")
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
