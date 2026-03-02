from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class ResponseBase(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None  # allow arbitrary data payloads

class PaginationData(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

class PaginationResponse(ResponseBase):
    data: PaginationData
