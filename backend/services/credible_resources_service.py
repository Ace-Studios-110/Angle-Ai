import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import aiohttp
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResourceType(Enum):
    GOVERNMENT = "government"
    ACADEMIC = "academic"
    INDUSTRY = "industry"
    NEWS = "news"
    REGULATORY = "regulatory"
    PROFESSIONAL = "professional"

class CredibilityLevel(Enum):
    HIGHEST = "highest"  # Government, academic journals
    HIGH = "high"       # Industry reports, reputable news
    MEDIUM = "medium"   # Professional guidelines
    LOW = "low"         # General web sources

@dataclass
class CredibleResource:
    name: str
    url: str
    resource_type: ResourceType
    credibility_level: CredibilityLevel
    description: str
    jurisdiction: Optional[str] = None
    last_verified: Optional[datetime] = None
    categories: List[str] = None
    api_endpoint: Optional[str] = None
    requires_auth: bool = False

class CredibleResourcesManager:
    """Manages credible resources and data sources for RAG research"""
    
    def __init__(self):
        self.resources = self._initialize_resources()
        self.resource_cache = {}
        self.cache_expiry = timedelta(hours=24)
    
    def _initialize_resources(self) -> Dict[str, CredibleResource]:
        """Initialize comprehensive list of credible resources"""
        
        resources = {
            # Government Resources
            "california_sos": CredibleResource(
                name="California Secretary of State",
                url="https://www.sos.ca.gov",
                resource_type=ResourceType.GOVERNMENT,
                credibility_level=CredibilityLevel.HIGHEST,
                description="California business registration and compliance information",
                jurisdiction="California",
                categories=["business_formation", "compliance", "licensing"],
                api_endpoint="https://api.sos.ca.gov"
            ),
            "irs_gov": CredibleResource(
                name="Internal Revenue Service",
                url="https://www.irs.gov",
                resource_type=ResourceType.GOVERNMENT,
                credibility_level=CredibilityLevel.HIGHEST,
                description="Federal tax information and business requirements",
                jurisdiction="Federal",
                categories=["tax", "business_structure", "compliance"],
                api_endpoint="https://api.irs.gov"
            ),
            "sba_gov": CredibleResource(
                name="Small Business Administration",
                url="https://www.sba.gov",
                resource_type=ResourceType.GOVERNMENT,
                credibility_level=CredibilityLevel.HIGHEST,
                description="Small business resources, funding, and guidance",
                jurisdiction="Federal",
                categories=["funding", "business_planning", "resources"],
                api_endpoint="https://api.sba.gov"
            ),
            "sec_gov": CredibleResource(
                name="Securities and Exchange Commission",
                url="https://www.sec.gov",
                resource_type=ResourceType.GOVERNMENT,
                credibility_level=CredibilityLevel.HIGHEST,
                description="Securities regulations and corporate compliance",
                jurisdiction="Federal",
                categories=["securities", "compliance", "corporate_governance"],
                api_endpoint="https://api.sec.gov"
            ),
            "ftc_gov": CredibleResource(
                name="Federal Trade Commission",
                url="https://www.ftc.gov",
                resource_type=ResourceType.GOVERNMENT,
                credibility_level=CredibilityLevel.HIGHEST,
                description="Consumer protection and business regulations",
                jurisdiction="Federal",
                categories=["consumer_protection", "advertising", "privacy"],
                api_endpoint="https://api.ftc.gov"
            ),
            
            # Academic Resources
            "harvard_business_review": CredibleResource(
                name="Harvard Business Review",
                url="https://hbr.org",
                resource_type=ResourceType.ACADEMIC,
                credibility_level=CredibilityLevel.HIGHEST,
                description="Leading business management publication",
                categories=["strategy", "management", "leadership", "innovation"],
                api_endpoint="https://api.hbr.org"
            ),
            "google_scholar": CredibleResource(
                name="Google Scholar",
                url="https://scholar.google.com",
                resource_type=ResourceType.ACADEMIC,
                credibility_level=CredibilityLevel.HIGHEST,
                description="Academic research and scholarly articles",
                categories=["research", "academic_papers", "studies"],
                api_endpoint="https://api.scholar.google.com"
            ),
            "jstor": CredibleResource(
                name="JSTOR",
                url="https://www.jstor.org",
                resource_type=ResourceType.ACADEMIC,
                credibility_level=CredibilityLevel.HIGHEST,
                description="Digital library of academic journals and books",
                categories=["academic_journals", "research", "studies"],
                api_endpoint="https://api.jstor.org",
                requires_auth=True
            ),
            "mit_sloan": CredibleResource(
                name="MIT Sloan Management Review",
                url="https://sloanreview.mit.edu",
                resource_type=ResourceType.ACADEMIC,
                credibility_level=CredibilityLevel.HIGHEST,
                description="Management research and insights",
                categories=["management", "strategy", "technology", "innovation"],
                api_endpoint="https://api.sloanreview.mit.edu"
            ),
            
            # Industry Resources
            "forbes": CredibleResource(
                name="Forbes",
                url="https://www.forbes.com",
                resource_type=ResourceType.INDUSTRY,
                credibility_level=CredibilityLevel.HIGH,
                description="Business news and industry insights",
                categories=["business_news", "entrepreneurship", "finance", "technology"],
                api_endpoint="https://api.forbes.com"
            ),
            "mckinsey": CredibleResource(
                name="McKinsey & Company",
                url="https://www.mckinsey.com",
                resource_type=ResourceType.INDUSTRY,
                credibility_level=CredibilityLevel.HIGH,
                description="Management consulting insights and research",
                categories=["strategy", "consulting", "industry_analysis"],
                api_endpoint="https://api.mckinsey.com"
            ),
            "deloitte": CredibleResource(
                name="Deloitte Insights",
                url="https://www2.deloitte.com/insights",
                resource_type=ResourceType.INDUSTRY,
                credibility_level=CredibilityLevel.HIGH,
                description="Professional services insights and research",
                categories=["consulting", "technology", "finance", "risk"],
                api_endpoint="https://api.deloitte.com"
            ),
            "pwc": CredibleResource(
                name="PwC Insights",
                url="https://www.pwc.com/us/en/industries/technology/insights.html",
                resource_type=ResourceType.INDUSTRY,
                credibility_level=CredibilityLevel.HIGH,
                description="Professional services and industry insights",
                categories=["consulting", "technology", "finance", "strategy"],
                api_endpoint="https://api.pwc.com"
            ),
            
            # News Resources
            "wall_street_journal": CredibleResource(
                name="The Wall Street Journal",
                url="https://www.wsj.com",
                resource_type=ResourceType.NEWS,
                credibility_level=CredibilityLevel.HIGH,
                description="Financial and business news",
                categories=["finance", "business_news", "markets", "economy"],
                api_endpoint="https://api.wsj.com",
                requires_auth=True
            ),
            "bloomberg": CredibleResource(
                name="Bloomberg",
                url="https://www.bloomberg.com",
                resource_type=ResourceType.NEWS,
                credibility_level=CredibilityLevel.HIGH,
                description="Financial news and market data",
                categories=["finance", "markets", "economy", "business_news"],
                api_endpoint="https://api.bloomberg.com",
                requires_auth=True
            ),
            "reuters": CredibleResource(
                name="Reuters",
                url="https://www.reuters.com",
                resource_type=ResourceType.NEWS,
                credibility_level=CredibilityLevel.HIGH,
                description="International news and business coverage",
                categories=["news", "business", "finance", "markets"],
                api_endpoint="https://api.reuters.com"
            ),
            "cnbc": CredibleResource(
                name="CNBC",
                url="https://www.cnbc.com",
                resource_type=ResourceType.NEWS,
                credibility_level=CredibilityLevel.HIGH,
                description="Business and financial news",
                categories=["finance", "business_news", "markets", "economy"],
                api_endpoint="https://api.cnbc.com"
            ),
            
            # Regulatory Resources
            "fda_gov": CredibleResource(
                name="Food and Drug Administration",
                url="https://www.fda.gov",
                resource_type=ResourceType.REGULATORY,
                credibility_level=CredibilityLevel.HIGHEST,
                description="Food and drug regulations and compliance",
                jurisdiction="Federal",
                categories=["food_safety", "drug_regulation", "medical_devices"],
                api_endpoint="https://api.fda.gov"
            ),
            "epa_gov": CredibleResource(
                name="Environmental Protection Agency",
                url="https://www.epa.gov",
                resource_type=ResourceType.REGULATORY,
                credibility_level=CredibilityLevel.HIGHEST,
                description="Environmental regulations and compliance",
                jurisdiction="Federal",
                categories=["environmental", "compliance", "sustainability"],
                api_endpoint="https://api.epa.gov"
            ),
            "osha_gov": CredibleResource(
                name="Occupational Safety and Health Administration",
                url="https://www.osha.gov",
                resource_type=ResourceType.REGULATORY,
                credibility_level=CredibilityLevel.HIGHEST,
                description="Workplace safety regulations",
                jurisdiction="Federal",
                categories=["safety", "compliance", "workplace"],
                api_endpoint="https://api.osha.gov"
            ),
            
            # Professional Resources
            "ama": CredibleResource(
                name="American Marketing Association",
                url="https://www.ama.org",
                resource_type=ResourceType.PROFESSIONAL,
                credibility_level=CredibilityLevel.HIGH,
                description="Marketing professional guidelines and resources",
                categories=["marketing", "advertising", "branding", "strategy"],
                api_endpoint="https://api.ama.org"
            ),
            "aicpa": CredibleResource(
                name="American Institute of CPAs",
                url="https://www.aicpa.org",
                resource_type=ResourceType.PROFESSIONAL,
                credibility_level=CredibilityLevel.HIGH,
                description="Accounting standards and professional guidelines",
                categories=["accounting", "auditing", "tax", "finance"],
                api_endpoint="https://api.aicpa.org"
            ),
            "sba_learning_center": CredibleResource(
                name="SBA Learning Center",
                url="https://www.sba.gov/learning-center",
                resource_type=ResourceType.PROFESSIONAL,
                credibility_level=CredibilityLevel.HIGH,
                description="Small business education and training resources",
                categories=["education", "training", "business_planning"],
                api_endpoint="https://api.sba.gov/learning"
            )
        }
        
        return resources
    
    async def get_resources_by_category(self, category: str) -> List[CredibleResource]:
        """Get resources filtered by category"""
        return [
            resource for resource in self.resources.values()
            if category in resource.categories
        ]
    
    async def get_resources_by_credibility(self, credibility_level: CredibilityLevel) -> List[CredibleResource]:
        """Get resources filtered by credibility level"""
        return [
            resource for resource in self.resources.values()
            if resource.credibility_level == credibility_level
        ]
    
    async def get_resources_by_jurisdiction(self, jurisdiction: str) -> List[CredibleResource]:
        """Get resources filtered by jurisdiction"""
        return [
            resource for resource in self.resources.values()
            if resource.jurisdiction and jurisdiction.lower() in resource.jurisdiction.lower()
        ]
    
    async def validate_resource_accessibility(self, resource: CredibleResource) -> bool:
        """Validate if a resource is accessible and up-to-date"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(resource.url, timeout=10) as response:
                    if response.status == 200:
                        resource.last_verified = datetime.now()
                        return True
                    return False
        except Exception as e:
            logger.warning(f"Failed to validate resource {resource.name}: {e}")
            return False
    
    async def get_resource_data(self, resource: CredibleResource, query: str) -> Dict[str, Any]:
        """Get data from a specific resource"""
        cache_key = f"{resource.name}_{hash(query)}"
        
        # Check cache first
        if cache_key in self.resource_cache:
            cached_data, timestamp = self.resource_cache[cache_key]
            if datetime.now() - timestamp < self.cache_expiry:
                return cached_data
        
        try:
            # Simulate API call (in real implementation, you'd make actual API calls)
            data = await self._fetch_resource_data(resource, query)
            
            # Cache the result
            self.resource_cache[cache_key] = (data, datetime.now())
            
            return data
        except Exception as e:
            logger.error(f"Failed to fetch data from {resource.name}: {e}")
            return {"error": str(e), "resource": resource.name}
    
    async def _fetch_resource_data(self, resource: CredibleResource, query: str) -> Dict[str, Any]:
        """Simulate fetching data from a resource (replace with actual API calls)"""
        # This is a placeholder - in real implementation, you'd make actual API calls
        return {
            "resource": resource.name,
            "query": query,
            "data": f"Sample data from {resource.name} for query: {query}",
            "credibility_level": resource.credibility_level.value,
            "categories": resource.categories,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_comprehensive_research_sources(self, query: str, business_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive research sources for a query"""
        
        # Determine relevant categories based on query and business context
        relevant_categories = self._determine_relevant_categories(query, business_context)
        
        # Get resources for each category
        research_sources = {}
        for category in relevant_categories:
            resources = await self.get_resources_by_category(category)
            research_sources[category] = resources
        
        # Add jurisdiction-specific resources
        if business_context.get('location'):
            jurisdiction_resources = await self.get_resources_by_jurisdiction(business_context['location'])
            research_sources['jurisdiction'] = jurisdiction_resources
        
        # Prioritize by credibility
        prioritized_sources = self._prioritize_sources_by_credibility(research_sources)
        
        return {
            "query": query,
            "business_context": business_context,
            "research_sources": prioritized_sources,
            "total_sources": sum(len(sources) for sources in research_sources.values()),
            "credibility_distribution": self._get_credibility_distribution(research_sources),
            "generated_at": datetime.now().isoformat()
        }
    
    def _determine_relevant_categories(self, query: str, business_context: Dict[str, Any]) -> List[str]:
        """Determine relevant categories based on query and business context"""
        categories = []
        
        query_lower = query.lower()
        industry = business_context.get('industry', '').lower()
        
        # Legal and compliance
        if any(term in query_lower for term in ['legal', 'compliance', 'regulation', 'permit', 'license']):
            categories.extend(['business_formation', 'compliance', 'licensing'])
        
        # Financial
        if any(term in query_lower for term in ['financial', 'funding', 'budget', 'tax', 'accounting']):
            categories.extend(['tax', 'funding', 'finance'])
        
        # Marketing
        if any(term in query_lower for term in ['marketing', 'branding', 'advertising', 'customer']):
            categories.extend(['marketing', 'advertising', 'branding'])
        
        # Operations
        if any(term in query_lower for term in ['operations', 'supply', 'equipment', 'process']):
            categories.extend(['strategy', 'management'])
        
        # Industry-specific
        if industry:
            if 'tech' in industry or 'software' in industry:
                categories.extend(['technology', 'innovation'])
            elif 'health' in industry or 'medical' in industry:
                categories.extend(['food_safety', 'drug_regulation'])
            elif 'manufacturing' in industry:
                categories.extend(['safety', 'compliance'])
        
        return list(set(categories))  # Remove duplicates
    
    def _prioritize_sources_by_credibility(self, research_sources: Dict[str, List[CredibleResource]]) -> Dict[str, List[CredibleResource]]:
        """Prioritize sources by credibility level"""
        prioritized = {}
        
        for category, resources in research_sources.items():
            # Sort by credibility level (highest first)
            sorted_resources = sorted(
                resources,
                key=lambda r: list(CredibilityLevel).index(r.credibility_level),
                reverse=True
            )
            prioritized[category] = sorted_resources
        
        return prioritized
    
    def _get_credibility_distribution(self, research_sources: Dict[str, List[CredibleResource]]) -> Dict[str, int]:
        """Get distribution of credibility levels"""
        distribution = {}
        
        for resources in research_sources.values():
            for resource in resources:
                level = resource.credibility_level.value
                distribution[level] = distribution.get(level, 0) + 1
        
        return distribution

# Global instance
credible_resources_manager = CredibleResourcesManager()

# Convenience functions
async def get_credible_resources_for_query(query: str, business_context: Dict[str, Any]) -> Dict[str, Any]:
    """Get credible resources for a specific query"""
    return await credible_resources_manager.get_comprehensive_research_sources(query, business_context)

async def validate_resource_credibility(resource_name: str) -> bool:
    """Validate if a resource is credible and accessible"""
    if resource_name in credible_resources_manager.resources:
        resource = credible_resources_manager.resources[resource_name]
        return await credible_resources_manager.validate_resource_accessibility(resource)
    return False

async def get_resources_by_category(category: str) -> List[CredibleResource]:
    """Get resources by category"""
    return await credible_resources_manager.get_resources_by_category(category)
