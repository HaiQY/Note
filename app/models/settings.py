from sqlalchemy import Column, String, Integer
from app.database import Base
from app.models.base import TimestampMixin


class Settings(TimestampMixin, Base):
    __tablename__ = "settings"

    key = Column(String(50), unique=True, nullable=False, index=True)
    value = Column(String(500))
    description = Column(String(200))