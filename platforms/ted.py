from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
import httpx
from base.platform import BasePlatform
from base.models import TenderResponse
from platforms import register_platform

class TEDSearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query text")
    country: Optional[str] = Field(None, description="Country code (SI, DE, etc.)")
    cpv_codes: Optional[List[str]] = Field(None, description="CPV commodity codes")
    publication_date_from: Optional[date] = Field(None, description="Publication date from")
    publication_date_to: Optional[date] = Field(None, description="Publication date to")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Number of results")
    offset: Optional[int] = Field(0, ge=0, description="Results offset")

class TEDPlatform(BasePlatform):
    """TED Europe platform implementation"""
    
    def get_platform_name(self) -> str:
        return "TED Europe"
    
    def get_base_url(self) -> str:
        return "https://ted.europa.eu/api"
    
    async def search(self, **kwargs) -> TenderResponse:
        """Search TED Europe database"""
        # Convert kwargs to TEDSearchRequest
        search_request = TEDSearchRequest(**kwargs)
        
        # Build API parameters
        params = {
            "limit": search_request.limit,
            "offset": search_request.offset
        }
        
        if search_request.query:
            params["q"] = search_request.query
        if search_request.country:
            params["country"] = search_request.country
        if search_request.cpv_codes:
            params["cpv"] = ",".join(search_request.cpv_codes)
        if search_request.publication_date_from:
            params["dateFrom"] = search_request.publication_date_from.isoformat()
        if search_request.publication_date_to:
            params["dateTo"] = search_request.publication_date_to.isoformat()
        
        url = f"{self.base_url}/v3/notices/search"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                data = await self.make_api_request(client, url, params=params)
                
                # Process results
                results = []
                if "results" in data:
                    for notice in data["results"]:
                        processed_notice = {
                            "id": notice.get("noticeId"),
                            "title": notice.get("title"),
                            "publication_date": notice.get("publicationDate"),
                            "deadline": notice.get("deadline"),
                            "country": notice.get("country"),
                            "contracting_authority": notice.get("contractingAuthority"),
                            "cpv_codes": notice.get("cpvCodes", []),
                            "estimated_value": notice.get("estimatedValue"),
                            "procedure_type": notice.get("procedureType"),
                            "url": f"https://ted.europa.eu/udl?uri=TED:NOTICE:{notice.get('noticeId')}"
                        }
                        results.append(processed_notice)
                
                return TenderResponse(
                    platform=self.platform_name,
                    total_count=data.get("totalCount", 0),
                    results=results,
                    query_info={
                        "search_params": search_request.dict(exclude_none=True),
                        "api_url": url
                    }
                )
        except Exception as e:
            return self.create_error_response(str(e))

# Register platform
register_platform("ted", TEDPlatform)