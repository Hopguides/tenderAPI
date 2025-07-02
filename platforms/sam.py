from pydantic import BaseModel, Field
from typing import Optional
import httpx
import os
from base.platform import BasePlatform
from base.models import TenderResponse
from platforms import register_platform

class SAMSearchRequest(BaseModel):
    posted_from: str = Field(..., description="Posted from date (MM/DD/YYYY)")
    posted_to: str = Field(..., description="Posted to date (MM/DD/YYYY)")
    dept_name: Optional[str] = Field(None, description="Department name")
    naics_code: Optional[str] = Field(None, description="NAICS code")
    ptype: Optional[str] = Field("o", description="Procurement type (o=solicitation, a=award)")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Number of results")
    offset: Optional[int] = Field(0, ge=0, description="Results offset")

class SAMPlatform(BasePlatform):
    """SAM.gov platform implementation"""
    
    def get_platform_name(self) -> str:
        return "SAM.gov"
    
    def get_base_url(self) -> str:
        return "https://api.sam.gov"
    
    def get_auth_requirements(self) -> dict:
        return {
            "required": True,
            "type": "api_key",
            "env_var": "SAM_API_KEY",
            "instructions": "Get API key from sam.gov/profile/details"
        }
    
    def get_headers(self) -> dict:
        api_key = os.getenv("SAM_API_KEY", "YOUR_SAM_API_KEY")
        return {
            "X-Api-Key": api_key,
            "Accept": "application/json"
        }
    
    async def search(self, **kwargs) -> TenderResponse:
        """Search SAM.gov opportunities"""
        search_request = SAMSearchRequest(**kwargs)
        
        # Build parameters
        params = {
            "limit": search_request.limit,
            "offset": search_request.offset,
            "postedFrom": search_request.posted_from,
            "postedTo": search_request.posted_to,
            "ptype": search_request.ptype
        }
        
        if search_request.dept_name:
            params["deptname"] = search_request.dept_name
        if search_request.naics_code:
            params["naics"] = search_request.naics_code
        
        url = f"{self.base_url}/prod/opportunities/v2/search"
        headers = self.get_headers()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                data = await self.make_api_request(client, url, headers=headers, params=params)
                
                # Process results
                results = []
                if "opportunitiesData" in data:
                    for opp in data["opportunitiesData"]:
                        processed_opp = {
                            "id": opp.get("noticeId"),
                            "title": opp.get("title"),
                            "solicitation_number": opp.get("solicitationNumber"),
                            "department": opp.get("department"),
                            "office": opp.get("office"),
                            "posted_date": opp.get("postedDate"),
                            "response_deadline": opp.get("responseDeadLine"),
                            "type": opp.get("type"),
                            "naics_code": opp.get("naicsCode"),
                            "set_aside_type": opp.get("typeOfSetAsideDescription"),
                            "active": opp.get("active"),
                            "url": f"https://sam.gov/opp/{opp.get('noticeId')}"
                        }
                        
                        # Add award info if available
                        if "award" in opp:
                            award = opp["award"]
                            processed_opp["award"] = {
                                "date": award.get("date"),
                                "number": award.get("number"),
                                "amount": award.get("amount"),
                                "awardee": award.get("awardee", {}).get("name")
                            }
                        
                        results.append(processed_opp)
                
                return TenderResponse(
                    platform=self.platform_name,
                    total_count=data.get("totalRecords", 0),
                    results=results,
                    query_info={
                        "search_params": search_request.dict(exclude_none=True),
                        "api_url": url
                    }
                )
        except Exception as e:
            return self.create_error_response(str(e))

# Register platform
register_platform("sam", SAMPlatform)