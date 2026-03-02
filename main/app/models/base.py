from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from app.database import Base

class TimestampMixin:
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
