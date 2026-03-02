from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    keywords: Optional[List[str]] = []
    color: str = "#3498db"
    icon: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    keywords: List[str] = []
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime
