from sqlalchemy import Column, String, Text, Boolean, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin
from app.models.json_mixin import JSONColumnMixin

class Note(JSONColumnMixin, TimestampMixin, Base):
    __tablename__ = "notes"
    
    title = Column(String(200))
    content = Column(Text)
    clean_content = Column(Text)
    image_path = Column(String(500), nullable=False)
    markdown_path = Column(String(500))
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    keywords = Column(Text, default="[]")
    is_important = Column(Boolean, default=False)
    status = Column(String(20), default="draft")
    ocr_confidence = Column(Float)
    source = Column(String(50), default="upload")
    extra_data = Column(Text, default="{}")
    
    category = relationship("Category", back_populates="notes")
    review_cards = relationship("ReviewCard", back_populates="note", cascade="all, delete-orphan")
    
    def get_keywords_list(self) -> list:
        return self.get_json_list("keywords")
    
    def set_keywords_list(self, keywords: list):
        self.set_json_list("keywords", keywords)
    
    def get_extra_data(self) -> dict:
        return self.get_json_dict("extra_data")
    
    def set_extra_data(self, data: dict):
        self.set_json_dict("extra_data", data)