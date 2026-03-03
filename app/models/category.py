from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin
from app.models.json_mixin import JSONColumnMixin

class Category(JSONColumnMixin, TimestampMixin, Base):
    __tablename__ = "categories"
    
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    keywords = Column(Text, default="[]")
    color = Column(String(7), default="#3498db")
    icon = Column(String(50))
    sort_order = Column(Integer, default=0)
    
    notes = relationship("Note", back_populates="category")
    
    def get_keywords_list(self) -> list:
        return self.get_json_list("keywords")
    
    def set_keywords_list(self, keywords: list):
        self.set_json_list("keywords", keywords)
