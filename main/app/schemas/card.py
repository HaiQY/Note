from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class CardBase(BaseModel):
    question: str
    answer: str
    card_type: str = "qa"
    difficulty: int = 3

class CardCreate(CardBase):
    note_id: int

class CardUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    card_type: Optional[str] = None
    difficulty: Optional[int] = None
    is_active: Optional[bool] = None

class CardResponse(CardBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    note_id: int
    next_review: Optional[datetime] = None
    interval: int = 1
    ease_factor: float = 2.5
    review_count: int = 0
    correct_count: int = 0
    last_review: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class CardGenerateRequest(BaseModel):
    count: int = 5
    card_types: List[str] = ["qa"]
    difficulty: str = "medium"

class CardReviewRequest(BaseModel):
    quality: int
    time_spent: Optional[int] = None

class CardReviewResponse(BaseModel):
    card_id: int
    next_review: datetime
    interval: int
    ease_factor: float
    review_count: int
