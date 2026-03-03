from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from app.config import DATABASE_URL, ensure_directories

ensure_directories()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    from app.models import note, category, card
    Base.metadata.create_all(bind=engine)
    
    from app.dao.category_dao import CategoryDAO
    from app.dao.settings_dao import SettingsDAO
    db = SessionLocal()
    try:
        CategoryDAO(db).init_default_categories()
        SettingsDAO(db).init_defaults()
    finally:
        db.close()

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
