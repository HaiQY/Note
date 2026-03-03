from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models.note import Note

class NoteDAO:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, skip: int = 0, limit: int = 20, category_id: int = None,
                is_important: bool = None, keyword: str = None) -> tuple[List[Note], int]:
        query = self.db.query(Note)
        
        if category_id:
            query = query.filter(Note.category_id == category_id)
        if is_important is not None:
            query = query.filter(Note.is_important == is_important)
        
        total = query.count()
        notes = query.order_by(Note.created_at.desc()).offset(skip).limit(limit).all()
        
        if keyword:
            notes = [n for n in notes if keyword in n.get_keywords_list()]
            total = len(notes)
        
        return notes, total
    
    def get_by_id(self, note_id: int) -> Optional[Note]:
        return self.db.query(Note).filter(Note.id == note_id).first()
    
    def create(self, image_path: str, title: str = None, content: str = None,
               category_id: int = None, keywords: List[str] = None,
               ocr_confidence: float = None, source: str = "upload") -> Note:
        note = Note(
            image_path=image_path,
            title=title,
            content=content,
            category_id=category_id,
            ocr_confidence=ocr_confidence,
            source=source,
            status="draft"
        )
        if keywords:
            note.set_keywords_list(keywords)
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note
    
    def update(self, note_id: int, **kwargs) -> Optional[Note]:
        note = self.get_by_id(note_id)
        if not note:
            return None
        for key, value in kwargs.items():
            if hasattr(note, key):
                if key == "keywords" and isinstance(value, list):
                    note.set_keywords_list(value)
                else:
                    setattr(note, key, value)
        note.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(note)
        return note
    
    def delete(self, note_id: int) -> bool:
        note = self.get_by_id(note_id)
        if not note:
            return False
        self.db.delete(note)
        self.db.commit()
        return True
    
    def search(self, query_text: str, category_id: int = None,
               date_from: datetime = None, date_to: datetime = None,
               limit: int = 50) -> List[Note]:
        query = self.db.query(Note)
        
        if query_text:
            query = query.filter(
                (Note.title.contains(query_text)) | 
                (Note.content.contains(query_text))
            )
        if category_id:
            query = query.filter(Note.category_id == category_id)
        if date_from:
            query = query.filter(Note.created_at >= date_from)
        if date_to:
            query = query.filter(Note.created_at <= date_to)
        
        return query.order_by(Note.created_at.desc()).limit(limit).all()
    
    def get_important(self, limit: int = 10) -> List[Note]:
        return self.db.query(Note).filter(
            Note.is_important == True
        ).order_by(Note.updated_at.desc()).limit(limit).all()
    
    def get_recent(self, limit: int = 10) -> List[Note]:
        return self.db.query(Note).order_by(Note.created_at.desc()).limit(limit).all()
