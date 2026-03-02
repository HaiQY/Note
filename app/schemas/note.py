from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class NoteBase(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
    keywords: Optional[List[str]] = []
    is_important: bool = False
    status: str = "draft"

class NoteCreate(NoteBase):
    image_path: str

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    clean_content: Optional[str] = None
    category_id: Optional[int] = None
    keywords: Optional[List[str]] = None
    is_important: Optional[bool] = None
    status: Optional[str] = None

class NoteResponse(NoteBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    image_path: str
    markdown_path: Optional[str] = None
    keywords: List[str] = []
    ocr_confidence: Optional[float] = None
    source: str = "upload"
    created_at: datetime
    updated_at: datetime
    category: Optional["CategoryBrief"] = None

class NoteBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: Optional[str] = None
    content_preview: Optional[str] = None
    image_path: str
    keywords: List[str] = []
    is_important: bool = False
    created_at: datetime
    category: Optional["CategoryBrief"] = None

class CategoryBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    color: str = "#3498db"

class NoteUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: Optional[str] = None
    content: Optional[str] = None
    image_path: str
    keywords: List[str] = []
    ocr_confidence: Optional[float] = None
    created_at: datetime
    category: Optional[CategoryBrief] = None

NoteResponse.model_rebuild()
NoteBrief.model_rebuild()
