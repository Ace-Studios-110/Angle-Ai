from openai import AsyncOpenAI
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import asyncio
from services.angel_service import conduct_web_search

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class RAGResearchEngine:
    """Retrieval Augmentation Generation engine for comprehensive research"""
    
    def __init__(self):
        self.authoritative_sources = {
            "government": [
                "sba.gov", "sec.gov", "irs.gov", "uspto.gov", "ftc.gov",
                "census.gov", "bls.gov", "ed.gov", "hhs.gov", "usda.gov"
            ],
            "academic": [
                "scholar.google.com", "jstor.org", "academia.edu", "researchgate.net",
                "harvard.edu", "stanford.edu", "mit.edu", "berkeley.edu"
            ],
            "industry_reports": [
                "forbes.com", "hbr.org", "bloomberg.com", "wsj.com", "reuters.com",
                "cnbc.com", "marketwatch.com", "businessinsider.com"
            ],
            "professional": [
                "linkedin.com", "clutch.co", "upwork.com", "glassdoor.com",
                "indeed.com", "ziprecruiter.com", "angellist.com"
            ],
            "legal": [
                "law.com", "martindale.com", "justia.com", "findlaw.com",
                "avvo.com", "lawyers.com", "nolo.com"
            ],
            "financial": [
                "bankrate.com", "nerdwallet.com", "investopedia.com", "fool.com",
                "morningstar.com", "yahoo.com/finance", "marketwatch.com"
            ]
        }
    
    async def conduct_comprehensive_research(self, query: str, business_context: Dict[str, Any], research_depth: str = "standard") -> Dict[str, Any]:
        """Conduct comprehensive research using multiple authoritative sources"""
        
        # Enhance query with business context
        enhanced_query = self._enhance_query(query, business_context)
        
        # Determine research scope based on depth
        research_sources = self._get_research_sources(research_depth)
        
        # Conduct parallel research across different source categories
        research_tasks = []
        for category, sources in research_sources.items():
            for source in sources:
                task = self._research_single_source(source, enhanced_query, category)
                research_tasks.append(task)
        
        # Execute research tasks in parallel
        research_results = await asyncio.gather(*research_tasks, return_exceptions=True)
        
        # Process and organize results
        organized_results = self._organize_research_results(research_results, research_sources)
        
        # Generate comprehensive analysis
        analysis = await self._generate_research_analysis(organized_results, query, business_context)
        
        return {
            "query": query,
            "enhanced_query": enhanced_query,
            "business_context": business_context,
            "research_depth": research_depth,
            "research_results": organized_results,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "sources_consulted": len([r for r in research_results if not isinstance(r, Exception)])
        }
    
    def _enhance_query(self, query: str, business_context: Dict[str, Any]) -> str:
        """Enhance query with business context for more targeted research"""
        
        enhancements = []
        
        if business_context.get('industry'):
            enhancements.append(f"industry: {business_context['industry']}")
        
        if business_context.get('location'):
            enhancements.append(f"location: {business_context['location']}")
        
        if business_context.get('business_type'):
            enhancements.append(f"business type: {business_context['business_type']}")
        
        if business_context.get('business_name'):
            enhancements.append(f"business: {business_context['business_name']}")
        
        # Add current year for relevance
        current_year = datetime.now().year
        enhancements.append(f"year: {current_year}")
        
        enhanced_query = f"{query}"
        if enhancements:
            enhanced_query += f" {' '.join(enhancements)}"
        
        return enhanced_query
    
    def _get_research_sources(self, depth: str) -> Dict[str, List[str]]:
        """Get research sources based on depth level"""
        
        if depth == "comprehensive":
            return self.authoritative_sources
        elif depth == "standard":
            # Return most important sources from each category
            return {
                "government": self.authoritative_sources["government"][:3],
                "academic": self.authoritative_sources["academic"][:2],
                "industry_reports": self.authoritative_sources["industry_reports"][:3],
                "professional": self.authoritative_sources["professional"][:2]
            }
        else:  # "basic"
            return {
                "government": self.authoritative_sources["government"][:2],
                "industry_reports": self.authoritative_sources["industry_reports"][:2]
            }
    
    async def _research_single_source(self, source: str, query: str, category: str) -> Dict[str, Any]:
        """Research a single source"""
        
        try:
            search_query = f"site:{source} {query}"
            result = await conduct_web_search(search_query)
            
            return {
                "source": source,
                "category": category,
                "query": search_query,
                "result": result if result and "unable to conduct web research" not in result else None,
                "success": result is not None and "unable to conduct web research" not in result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "source": source,
                "category": category,
                "query": f"site:{source} {query}",
                "result": None,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _organize_research_results(self, results: List[Any], research_sources: Dict[str, List[str]]) -> Dict[str, Any]:
        """Organize research results by category and success"""
        
        organized = {
            "by_category": {},
            "successful_sources": [],
            "failed_sources": [],
            "total_sources": 0,
            "successful_research": 0
        }
        
        for result in results:
            if isinstance(result, Exception):
                continue
            
            organized["total_sources"] += 1
            
            if result.get("success"):
                organized["successful_research"] += 1
                organized["successful_sources"].append(result["source"])
                
                category = result["category"]
                if category not in organized["by_category"]:
                    organized["by_category"][category] = []
                organized["by_category"][category].append(result)
            else:
                organized["failed_sources"].append({
                    "source": result["source"],
                    "error": result.get("error", "Unknown error")
                })
        
        return organized
    
    async def _generate_research_analysis(self, organized_results: Dict[str, Any], original_query: str, business_context: Dict[str, Any]) -> str:
        """Generate comprehensive analysis from research results"""
        
        # Prepare research data for analysis
        research_data = []
        for category, results in organized_results["by_category"].items():
            for result in results:
                if result["result"]:
                    research_data.append(f"Source: {result['source']} ({category})\n{result['result']}")
        
        if not research_data:
            return "No research data available for analysis."
        
        analysis_prompt = f"""
        Analyze the following research data and provide comprehensive insights for the business question: "{original_query}"
        
        Business Context:
        - Industry: {business_context.get('industry', 'General Business')}
        - Location: {business_context.get('location', 'United States')}
        - Business Type: {business_context.get('business_type', 'Startup')}
        
        Research Data:
        {chr(10).join(research_data[:10])}  # Limit to first 10 sources to avoid token limits
        
        Provide a comprehensive analysis that includes:
        1. Key Findings: Most important insights from the research
        2. Industry Trends: Current trends and developments
        3. Regulatory Requirements: Legal and compliance considerations
        4. Best Practices: Recommended approaches and strategies
        5. Market Opportunities: Potential opportunities identified
        6. Risk Factors: Potential challenges and risks
        7. Actionable Recommendations: Specific next steps
        
        Format the analysis as structured, actionable guidance that the user can immediately implement.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Analysis generation failed: {str(e)}"
    
    async def validate_user_input(self, user_input: str, business_context: Dict[str, Any], question_type: str) -> Dict[str, Any]:
        """Validate user input against research-backed standards"""
        
        # Determine validation criteria based on question type
        validation_criteria = self._get_validation_criteria(question_type, business_context)
        
        # Conduct research to validate the input
        validation_query = f"validate {question_type} {user_input} {business_context.get('industry', '')}"
        research_results = await self.conduct_comprehensive_research(validation_query, business_context, "standard")
        
        # Generate validation analysis
        validation_prompt = f"""
        Validate the following user input against industry standards and best practices:
        
        User Input: "{user_input}"
        Question Type: {question_type}
        Business Context: {business_context}
        
        Validation Criteria: {validation_criteria}
        
        Research Data: {research_results['analysis']}
        
        Provide validation results including:
        1. Accuracy Assessment: Is the input accurate and realistic?
        2. Completeness Check: Is the input complete enough for the purpose?
        3. Industry Alignment: Does it align with industry standards?
        4. Risk Assessment: Are there any potential risks or issues?
        5. Improvement Suggestions: How could the input be improved?
        6. Validation Score: Rate from 1-10 with explanation
        
        Format as structured validation report.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": validation_prompt}],
                temperature=0.2,
                max_tokens=1500
            )
            
            return {
                "user_input": user_input,
                "question_type": question_type,
                "validation_results": response.choices[0].message.content,
                "research_backing": research_results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "user_input": user_input,
                "question_type": question_type,
                "validation_results": f"Validation failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_validation_criteria(self, question_type: str, business_context: Dict[str, Any]) -> str:
        """Get validation criteria based on question type"""
        
        criteria_map = {
            "business_idea": "Innovation, market viability, competitive advantage, scalability",
            "financial_projections": "Realistic assumptions, industry benchmarks, growth rates, market size",
            "market_research": "Target market accuracy, competitive landscape, market size, customer needs",
            "legal_structure": "Compliance requirements, liability protection, tax implications, scalability",
            "marketing_strategy": "Target audience alignment, channel effectiveness, budget allocation, ROI potential",
            "operations": "Efficiency, scalability, resource requirements, quality control",
            "team_building": "Skill requirements, compensation benchmarks, organizational structure",
            "funding": "Funding amount justification, use of funds, investor expectations, valuation"
        }
        
        return criteria_map.get(question_type, "General business standards and best practices")
    
    async def generate_educational_insights(self, user_response: str, question_context: str, business_context: Dict[str, Any]) -> str:
        """Generate educational insights based on user response and research"""
        
        # Conduct research for educational insights
        insight_query = f"educational insights {question_context} {user_response} {business_context.get('industry', '')}"
        research_results = await self.conduct_comprehensive_research(insight_query, business_context, "standard")
        
        # Generate educational insights
        insights_prompt = f"""
        Generate educational insights based on the user's response and comprehensive research:
        
        User Response: "{user_response}"
        Question Context: "{question_context}"
        Business Context: {business_context}
        
        Research Data: {research_results['analysis']}
        
        Provide educational insights that include:
        1. Industry Context: How this applies to their specific industry
        2. Economic Factors: Relevant economic considerations and trends
        3. Best Practices: Industry best practices and standards
        4. Common Pitfalls: What to avoid based on research
        5. Growth Opportunities: Potential opportunities for expansion
        6. Strategic Considerations: Long-term strategic implications
        
        Make the insights practical, actionable, and specific to their business context.
        Format as educational content that enhances their understanding.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": insights_prompt}],
                temperature=0.4,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Educational insights generation failed: {str(e)}"

class RAGServiceProviderEngine:
    """RAG engine specifically for service provider research and recommendations"""
    
    def __init__(self):
        self.provider_sources = {
            "legal": ["martindale.com", "lawyers.com", "avvo.com", "findlaw.com"],
            "financial": ["cpa.com", "aicpa.org", "bankrate.com", "nerdwallet.com"],
            "marketing": ["hubspot.com", "marketingland.com", "clutch.co", "upwork.com"],
            "operations": ["alibaba.com", "amazon.com", "linkedin.com", "indeed.com"],
            "technology": ["gartner.com", "forrester.com", "techcrunch.com", "wired.com"],
            "general": ["yelp.com", "google.com", "bbb.org", "angieslist.com"]
        }
    
    async def research_service_providers(self, service_type: str, business_context: Dict[str, Any], location: str = None) -> Dict[str, Any]:
        """Research service providers for a specific service type"""
        
        # Determine relevant sources for the service type
        relevant_sources = self.provider_sources.get(service_type, self.provider_sources["general"])
        
        # Enhance search query with location and business context
        search_query = f"{service_type} services {business_context.get('industry', '')}"
        if location:
            search_query += f" {location}"
        
        # Conduct research across multiple sources
        research_tasks = []
        for source in relevant_sources:
            task = self._research_provider_source(source, search_query, service_type)
            research_tasks.append(task)
        
        # Execute research tasks
        research_results = await asyncio.gather(*research_tasks, return_exceptions=True)
        
        # Process and organize provider data
        providers = self._extract_provider_data(research_results, service_type, business_context)
        
        # Generate provider recommendations
        recommendations = await self._generate_provider_recommendations(providers, service_type, business_context)
        
        return {
            "service_type": service_type,
            "business_context": business_context,
            "location": location,
            "providers_found": len(providers),
            "providers": providers,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _research_provider_source(self, source: str, query: str, service_type: str) -> Dict[str, Any]:
        """Research providers from a single source"""
        
        try:
            search_query = f"site:{source} {query}"
            result = await conduct_web_search(search_query)
            
            return {
                "source": source,
                "service_type": service_type,
                "query": search_query,
                "result": result if result and "unable to conduct web research" not in result else None,
                "success": result is not None and "unable to conduct web research" not in result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "source": source,
                "service_type": service_type,
                "query": f"site:{source} {query}",
                "result": None,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_provider_data(self, research_results: List[Any], service_type: str, business_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract provider data from research results"""
        
        providers = []
        
        for result in research_results:
            if isinstance(result, Exception) or not result.get("success"):
                continue
            
            # Parse provider information from research results
            provider_data = self._parse_provider_info(result["result"], service_type)
            if provider_data:
                providers.extend(provider_data)
        
        # Remove duplicates and limit results
        unique_providers = self._deduplicate_providers(providers)
        return unique_providers[:10]  # Limit to top 10 providers
    
    def _parse_provider_info(self, research_text: str, service_type: str) -> List[Dict[str, Any]]:
        """Parse provider information from research text"""
        
        # This is a simplified parser - in a real implementation, you'd use more sophisticated NLP
        providers = []
        
        # Look for common provider patterns
        lines = research_text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 10 and any(keyword in line.lower() for keyword in ['service', 'consulting', 'agency', 'firm', 'company']):
                # Extract basic provider information
                provider = {
                    "name": line[:100],  # Simplified - would need better parsing
                    "type": service_type,
                    "description": line,
                    "local": False,  # Would need location detection
                    "source": "research"
                }
                providers.append(provider)
        
        return providers
    
    def _deduplicate_providers(self, providers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate providers"""
        
        seen_names = set()
        unique_providers = []
        
        for provider in providers:
            name_key = provider["name"].lower().strip()
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_providers.append(provider)
        
        return unique_providers
    
    async def _generate_provider_recommendations(self, providers: List[Dict[str, Any]], service_type: str, business_context: Dict[str, Any]) -> str:
        """Generate provider recommendations based on research"""
        
        if not providers:
            return "No specific providers found in research. Consider searching local business directories or professional networks."
        
        recommendations_prompt = f"""
        Generate service provider recommendations based on the following research:
        
        Service Type: {service_type}
        Business Context: {business_context}
        Providers Found: {len(providers)}
        
        Provider Data: {json.dumps(providers[:5], indent=2)}  # Limit to first 5 for token management
        
        Provide recommendations that include:
        1. Top 3-5 recommended providers with rationale
        2. Key considerations for selection
        3. Questions to ask when evaluating providers
        4. Red flags to watch out for
        5. Expected costs and timelines
        
        Format as actionable recommendations that help the user make informed decisions.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": recommendations_prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Provider recommendations generation failed: {str(e)}"

# Global instances
rag_engine = RAGResearchEngine()
rag_provider_engine = RAGServiceProviderEngine()

# Convenience functions
async def conduct_rag_research(query: str, business_context: Dict[str, Any], depth: str = "standard") -> Dict[str, Any]:
    """Conduct comprehensive RAG research"""
    return await rag_engine.conduct_comprehensive_research(query, business_context, depth)

async def validate_with_rag(user_input: str, business_context: Dict[str, Any], question_type: str) -> Dict[str, Any]:
    """Validate user input using RAG research"""
    return await rag_engine.validate_user_input(user_input, business_context, question_type)

async def generate_rag_insights(user_response: str, question_context: str, business_context: Dict[str, Any]) -> str:
    """Generate educational insights using RAG"""
    return await rag_engine.generate_educational_insights(user_response, question_context, business_context)

async def research_service_providers_rag(service_type: str, business_context: Dict[str, Any], location: str = None) -> Dict[str, Any]:
    """Research service providers using RAG"""
    return await rag_provider_engine.research_service_providers(service_type, business_context, location)
