from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import httpx
from bs4 import BeautifulSoup
import asyncio
import re
from .models import TenderResponse

class BasePlatform(ABC):
    """Base class za vse tender platforme"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.platform_name = self.get_platform_name()
        self.base_url = self.get_base_url()
        self.requires_auth = self.get_auth_requirements()
        
    @abstractmethod
    def get_platform_name(self) -> str:
        """Return platform name"""
        pass
    
    @abstractmethod
    def get_base_url(self) -> str:
        """Return base URL for platform"""
        pass
    
    @abstractmethod
    async def search(self, **kwargs) -> TenderResponse:
        """Main search method - implement per platform"""
        pass
    
    def get_auth_requirements(self) -> Dict[str, Any]:
        """Override if platform needs authentication"""
        return {"required": False}
    
    def get_search_params_schema(self) -> Dict[str, Any]:
        """Override to define search parameters"""
        return {}
    
    # Helper methods for all platforms
    async def make_api_request(self, client: httpx.AsyncClient, url: str, 
                             headers: Dict[str, str] = None, 
                             params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Standard API request"""
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"API request failed: {str(e)}")
    
    async def make_scraping_request(self, client: httpx.AsyncClient, 
                                  url: str, headers: Dict[str, str] = None) -> BeautifulSoup:
        """Standard web scraping request"""
        try:
            if not headers:
                headers = self.get_default_headers()
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            await asyncio.sleep(1)  # Be respectful
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            raise Exception(f"Scraping request failed: {str(e)}")
    
    def get_default_headers(self) -> Dict[str, str]:
        """Default headers for web scraping"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
    
    def clean_text(self, text: str) -> str:
        """Clean scraped text"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())
    
    def create_error_response(self, error_msg: str) -> TenderResponse:
        """Standard error response"""
        return TenderResponse(
            platform=self.platform_name,
            total_count=0,
            results=[],
            query_info={"error": error_msg},
            status="error",
            error=error_msg
        )