from openai import AsyncOpenAI
import os

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_full_business_plan(history):
    BUSINESS_PLAN_TEMPLATE = """
### 1. Executive Summary
Brief overview of the startup and business concept.

### 2. Business Overview
- Business model and vision
- Legal structure
- Value proposition

### 3. Market Analysis
- Target audience
- Industry trends (use web context)
- Competitor landscape in bullet/table format

### 4. Angel Research
- Include researched insights: market gaps, benchmarks, pricing, etc.

### 5. Product or Service Details
- Description
- Features/Benefits
- Pricing or revenue model

### 6. Marketing & Sales Strategy
- Channels
- Branding tone
- Customer journey

### 7. Operations Plan
- Daily workflows
- Key tools or technologies
- Staffing roles (if any)

### 8. Financial Overview
- Expected monthly/annual revenue
- Cost structure
- Break-even timeline (if estimable)

### 9. Challenges & Risk Mitigation
- Possible risks
- Contingency strategies

### 10. Next Steps & Milestones
- Short-term goals
- Suggested timelines

**Formatting Requirements:**
- Use **bold** for action words and key terms
- Use bullet points wherever possible
- Use tables for pricing/comparison if applicable
- Use a professional tone
- Ensure ReactMarkdown compatibility (clean Markdown)
"""

    messages = [
        {
            "role": "system",
            "content": (
                "You are Angel, an expert AI business strategist. "
                "You must generate a complete and professional business plan for a startup. "
                "Use clean, ReactMarkdown-compatible formatting. "
                "Strictly follow the provided markdown structure and respond only with the business plan content."
            )
        },
        {
            "role": "user",
            "content": (
                f"Based on the user's KYC and business plan answers below, generate a detailed business plan. "
                f"Follow the exact markdown format and content outline below:\n\n"
                f"{BUSINESS_PLAN_TEMPLATE}\n\n"
                f"== USER RESPONSES ==\n{history}"
            )
        }
    ]

    response = await client.chat.completions.create(
        model="gpt-4o-search-preview",
        messages=messages,
    )

    return {
        "plan": response.choices[0].message.content.strip()
    }

async def generate_full_roadmap_plan(history):
    ROADMAP_TEMPLATE = """
### 1. Objective
Summarize the main goal and expected outcome.

### 2. Roadmap Steps
For each step include:
- **Timeline** (e.g., Week 1, Month 1)
- **Action**: Start with a verb (e.g., 'Launch campaign', 'Register domain')
- **Owner** (User, Angel, or Shared)
- **Recommended Tools/Vendors** (3 options in a table or bullet)

### 3. Tips for Success
- Industry-specific guidance
- Mistakes to avoid

### 4. ✅ Roadmap Launch Summary
A motivating closing paragraph that transitions the user to execution.

**Formatting Tips:**
- Bold all step titles and key terms
- Use bullet lists for clarity
- Use a professional but friendly tone
- Include tables for tools if possible
"""

    messages = [
        {
            "role": "system",
            "content": (
                "You are Angel, an AI startup coach specialized in crafting execution-ready business roadmaps. "
                "Based on the user’s KYC and Business Plan information, your job is to generate a practical, phased roadmap "
                "that guides the founder step-by-step to launch and grow their venture. "
                "You may use web search for realistic timelines, market constraints, and startup norms. "
                "Use clear, friendly tone, markdown formatting, and React-friendly output."
            )
        },
        {
            "role": "user",
            "content": (
                "Please create a **7–10 step startup roadmap** for the user based on their KYC and Business Plan answers below. "
                "If any ROADMAP responses are present in the history, use them to personalize further.\n\n"
                f"{ROADMAP_TEMPLATE}\n\n"
                "== CHAT HISTORY (KYC + BUSINESS PLAN + ROADMAP if any) ==\n"
                f"{history}"
            )
        }
    ]

    response = await client.chat.completions.create(
        model="gpt-4o-search-preview",
        messages=messages,
    )

    return {
        "plan": response.choices[0].message.content
    }
