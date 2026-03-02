from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin

class ReviewCard(TimestampMixin, Base):
    __tablename__ = "review_cards"
    
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    card_type = Column(String(20), default="qa")
    difficulty = Column(Integer, default=3)
    next_review = Column(DateTime)
    interval = Column(Integer, default=1)
    ease_factor = Column(Float, default=2.5)
    review_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    last_review = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    note = relationship("Note", back_populates="review_cards")
    review_logs = relationship("ReviewLog", back_populates="card", cascade="all, delete-orphan")

class ReviewLog(TimestampMixin, Base):
    __tablename__ = "review_logs"
    
    card_id = Column(Integer, ForeignKey("review_cards.id", ondelete="CASCADE"), nullable=False)
    quality = Column(Integer, nullable=False)
    reviewed_at = Column(DateTime, default=datetime.now, nullable=False)
    time_spent = Column(Integer)
    
    card = relationship("ReviewCard", back_populates="review_logs")
