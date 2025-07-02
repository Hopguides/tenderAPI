"""
Bonfire Platform Implementation
Government procurement platform used by many US states and municipalities
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
import httpx
from bs4 import BeautifulSoup
import re
from base.platform import BasePlatform
from base.models import TenderResponse
from platforms import register_platform


class BonfireSearchRequest(BaseModel):
    organization: str = Field(..., description="Organization/agency name to search")
    state: Optional[str] = Field(None, description="State code (e.g., 'CA', 'NY')")
    keywords: Optional[str] = Field(None, description="Keywords to search for")
    status: Optional[str] = Field("open", description="Tender status (open, closed, all)")
    limit: Optional[int] = Field(10, ge=1, le=50, description="Number of results")
    days_back: Optional[int] = Field(30, ge=1, le=365, description="Days to look back")


class BonfirePlatform(BasePlatform):
    """Bonfire procurement platform implementation"""
    
    def get_platform_name(self) -> str:
        return "Bonfire"
    
    def get_base_url(self) -> str:
        return "https://gobonfire.com"
    
    def get_search_params_schema(self) -> dict:
        return {
            "organization": {"type": "string", "required": True, "description": "Organization name"},
            "state": {"type": "string", "required": False, "description": "State code"},
            "keywords": {"type": "string", "required": False, "description": "Search keywords"},
            "status": {"type": "string", "required": False, "default": "open", "enum": ["open", "closed", "all"]},
            "limit": {"type": "integer", "required": False, "default": 10, "min": 1, "max": 50},
            "days_back": {"type": "integer", "required": False, "default": 30, "min": 1, "max": 365}
        }
    
    async def search(self, **kwargs) -> TenderResponse:
        """Search Bonfire platform for procurement opportunities"""
        try:
            # Validate input
            search_request = BonfireSearchRequest(**kwargs)
            
            # Build search URL - Bonfire uses organization-specific subdomains
            org_slug = self._normalize_organization_name(search_request.organization)
            search_url = f"https://{org_slug}.gobonfire.com/portal/solicitations"
            
            # Prepare search parameters
            params = {
                "status": search_request.status,
                "limit": search_request.limit
            }
            
            if search_request.keywords:
                params["search"] = search_request.keywords
            
            if search_request.state:
                params["state"] = search_request.state
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # First, try to access the organization's portal
                soup = await self.make_scraping_request(client, search_url)
                
                # Parse solicitations from the page
                results = await self._parse_bonfire_solicitations(soup, search_url, search_request)
                
                return TenderResponse(
                    platform=self.platform_name,
                    total_count=len(results),
                    tenders=[],  # Will be populated from results via backward compatibility
                    results=results,
                    query_info={
                        "search_params": search_request.dict(exclude_none=True),
                        "search_url": search_url,
                        "organization_slug": org_slug
                    }
                )
                
        except Exception as e:
            return self.create_error_response(f"Bonfire search failed: {str(e)}")
    
    def _normalize_organization_name(self, org_name: str) -> str:
        """Convert organization name to Bonfire subdomain format"""
        # Common organization name mappings
        org_mappings = {
            "california": "ca",
            "new york": "ny", 
            "texas": "tx",
            "florida": "fl",
            "illinois": "il",
            "pennsylvania": "pa",
            "ohio": "oh",
            "georgia": "ga",
            "north carolina": "nc",
            "michigan": "mi",
            "los angeles": "losangeles",
            "san francisco": "sf",
            "chicago": "chicago",
            "houston": "houston",
            "phoenix": "phoenix",
            "philadelphia": "philadelphia",
            "san antonio": "sanantonio",
            "san diego": "sandiego",
            "dallas": "dallas",
            "san jose": "sanjose"
        }
        
        # Normalize the organization name
        normalized = org_name.lower().strip()
        
        # Check if we have a direct mapping
        if normalized in org_mappings:
            return org_mappings[normalized]
        
        # Otherwise, create a slug from the name
        slug = re.sub(r'[^a-z0-9]+', '', normalized)
        return slug[:20]  # Limit length
    
    async def _parse_bonfire_solicitations(self, soup: BeautifulSoup, base_url: str, 
                                         search_request: BonfireSearchRequest) -> List[dict]:
        """Parse solicitations from Bonfire HTML page"""
        results = []
        
        try:
            # Look for common Bonfire solicitation containers
            solicitation_selectors = [
                '.solicitation-item',
                '.tender-item', 
                '.opportunity-item',
                '.procurement-item',
                'tr[data-solicitation-id]',
                '.card.solicitation',
                '[data-testid="solicitation"]'
            ]
            
            solicitations = []
            for selector in solicitation_selectors:
                found = soup.select(selector)
                if found:
                    solicitations = found
                    break
            
            # If no specific containers found, look for table rows or list items
            if not solicitations:
                solicitations = soup.select('tr:has(td), .list-item, .row')
            
            for idx, item in enumerate(solicitations[:search_request.limit]):
                try:
                    solicitation = self._extract_solicitation_data(item, base_url, idx)
                    if solicitation and self._is_relevant_solicitation(solicitation, search_request):
                        results.append(solicitation)
                except Exception as e:
                    # Skip problematic items but continue processing
                    continue
            
            # If we didn't find structured data, create a fallback result
            if not results:
                results.append({
                    "id": f"bonfire_{search_request.organization}_fallback",
                    "title": f"Bonfire Portal Access - {search_request.organization}",
                    "description": f"Access to {search_request.organization} procurement portal on Bonfire platform",
                    "organization": search_request.organization,
                    "platform_url": base_url,
                    "status": "portal_access",
                    "type": "portal_link",
                    "posted_date": None,
                    "deadline": None,
                    "estimated_value": None,
                    "contact_info": None,
                    "documents": [],
                    "categories": ["government", "procurement"],
                    "metadata": {
                        "platform": "Bonfire",
                        "access_type": "portal",
                        "note": "Direct portal access - manual browsing required"
                    }
                })
            
        except Exception as e:
            # Return error info as a result
            results.append({
                "id": f"bonfire_error_{search_request.organization}",
                "title": f"Bonfire Search Error - {search_request.organization}",
                "description": f"Error accessing Bonfire portal: {str(e)}",
                "organization": search_request.organization,
                "status": "error",
                "error": str(e)
            })
        
        return results
    
    def _extract_solicitation_data(self, item: BeautifulSoup, base_url: str, index: int) -> dict:
        """Extract solicitation data from HTML element"""
        try:
            # Extract title
            title_selectors = ['h3', 'h4', '.title', '.name', '.solicitation-title', 'td:first-child']
            title = self._extract_text_by_selectors(item, title_selectors) or f"Solicitation {index + 1}"
            
            # Extract description
            desc_selectors = ['.description', '.summary', '.details', 'td:nth-child(2)', 'p']
            description = self._extract_text_by_selectors(item, desc_selectors) or ""
            
            # Extract dates
            date_selectors = ['.date', '.posted', '.deadline', '.due-date', 'td:contains("/")', 'time']
            posted_date = self._extract_text_by_selectors(item, date_selectors)
            
            # Extract links
            link_elem = item.find('a', href=True)
            link_url = None
            if link_elem:
                href = link_elem['href']
                if href.startswith('/'):
                    link_url = base_url + href
                elif href.startswith('http'):
                    link_url = href
            
            # Extract ID
            solicitation_id = (
                item.get('data-solicitation-id') or 
                item.get('data-id') or 
                item.get('id') or 
                f"bonfire_{index}"
            )
            
            # Extract status
            status_selectors = ['.status', '.state', '.badge']
            status = self._extract_text_by_selectors(item, status_selectors) or "unknown"
            
            return {
                "id": solicitation_id,
                "title": self.clean_text(title)[:200],  # Limit title length
                "description": self.clean_text(description)[:500],  # Limit description
                "organization": "Bonfire Portal",
                "posted_date": self._parse_date_string(posted_date),
                "deadline": None,  # Would need more specific parsing
                "status": status.lower(),
                "type": "solicitation",
                "platform_url": link_url or base_url,
                "estimated_value": None,
                "contact_info": None,
                "documents": [],
                "categories": ["government", "procurement", "bonfire"],
                "metadata": {
                    "platform": "Bonfire",
                    "extraction_method": "web_scraping",
                    "raw_html_length": len(str(item))
                }
            }
            
        except Exception as e:
            return {
                "id": f"bonfire_parse_error_{index}",
                "title": f"Parse Error {index + 1}",
                "description": f"Failed to parse solicitation: {str(e)}",
                "status": "parse_error",
                "error": str(e)
            }
    
    def _extract_text_by_selectors(self, element: BeautifulSoup, selectors: List[str]) -> str:
        """Try multiple selectors to extract text"""
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    # Handle pseudo-selectors manually
                    search_text = selector.split(':contains("')[1].split('")')[0]
                    found = element.find_all(text=lambda text: search_text in str(text) if text else False)
                    if found:
                        return str(found[0]).strip()
                else:
                    found = element.select_one(selector)
                    if found:
                        return found.get_text(strip=True)
            except Exception:
                continue
        return ""
    
    def _parse_date_string(self, date_str: str) -> str:
        """Parse various date formats"""
        if not date_str:
            return None
        
        # Clean the date string
        date_str = self.clean_text(date_str)
        
        # Look for common date patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
            r'\d{4}-\d{2}-\d{2}',      # YYYY-MM-DD
            r'\d{1,2}-\d{1,2}-\d{4}',  # MM-DD-YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                return match.group()
        
        return date_str[:20]  # Return first 20 chars if no pattern matches
    
    def _is_relevant_solicitation(self, solicitation: dict, search_request: BonfireSearchRequest) -> bool:
        """Check if solicitation matches search criteria"""
        if not solicitation or solicitation.get('status') == 'parse_error':
            return False
        
        # If keywords specified, check if they appear in title or description
        if search_request.keywords:
            keywords = search_request.keywords.lower()
            title = solicitation.get('title', '').lower()
            description = solicitation.get('description', '').lower()
            
            if keywords not in title and keywords not in description:
                return False
        
        # Filter by status if specified
        if search_request.status != "all":
            sol_status = solicitation.get('status', '').lower()
            if search_request.status == "open" and sol_status in ['closed', 'expired', 'awarded']:
                return False
            elif search_request.status == "closed" and sol_status in ['open', 'active']:
                return False
        
        return True


# Register the Bonfire platform
register_platform("bonfire", BonfirePlatform)


# Quick test function for development
async def test_bonfire_platform():
    """Test function for Bonfire platform"""
    platform = BonfirePlatform()
    
    test_searches = [
        {"organization": "california", "keywords": "IT services"},
        {"organization": "losangeles", "status": "open"},
        {"organization": "chicago", "limit": 5}
    ]
    
    for search in test_searches:
        print(f"\n🔍 Testing Bonfire search: {search}")
        result = await platform.search(**search)
        print(f"✅ Results: {result.total_count} found")
        if result.results:
            print(f"📋 First result: {result.results[0].get('title', 'No title')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_bonfire_platform())

