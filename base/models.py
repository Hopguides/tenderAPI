from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class TenderStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    AWARDED = "awarded"

class Tender(BaseModel):
    """Individual tender listing model"""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    organization: Optional[str] = None
    url: Optional[str] = None
    notice_id: Optional[str] = None
    posted_date: Optional[datetime] = None
    response_deadline: Optional[datetime] = None
    estimated_value: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None

class TenderResponse(BaseModel):
    """Response model for tender search results"""
    platform: str
    total_count: int
    tenders: List[Tender] = Field(default_factory=list)
    results: Optional[List[Dict[str, Any]]] = Field(default_factory=list)  # Backward compatibility
    query_info: Dict[str, Any] = Field(default_factory=dict)
    status: str = "success"
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Ensure backward compatibility - if results provided but not tenders, convert
        if self.results and not self.tenders:
            self.tenders = [Tender(**item) if isinstance(item, dict) else item for item in self.results]