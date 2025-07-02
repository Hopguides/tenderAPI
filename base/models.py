from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date
from enum import Enum

class TenderStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    AWARDED = "awarded"

class TenderResponse(BaseModel):
    platform: str
    total_count: int
    results: List[Dict[str, Any]]
    query_info: Dict[str, Any]
    status: str = "success"
    error: Optional[str] = None