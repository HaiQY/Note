from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin

class Category(TimestampMixin, Base):
    __tablename__ = "categories"
    
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    keywords = Column(Text, default="[]")
    color = Column(String(7), default="#3498db")
    icon = Column(String(50))
    sort_order = Column(Integer, default=0)
    
    notes = relationship("Note", back_populates="category")
    
    def get_keywords_list(self) -> list:
        import json
        try:
            return json.loads(self.keywords) if self.keywords else []
        except:
            return []
    
    def set_keywords_list(self, keywords: list):
        import json
        self.keywords = json.dumps(keywords, ensure_ascii=False)
