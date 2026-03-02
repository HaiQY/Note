from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from app.dao.note_dao import NoteDAO
from app.models.note import Note

class SearchService:
    def __init__(self, db: Session):
        self.note_dao = NoteDAO(db)
    
    def search(
        self,
        query: str,
        category_id: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
        limit: int = 50
    ) -> List[dict]:
        notes = self.note_dao.search(
            query_text=query,
            category_id=category_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit
        )
        
        results = []
        for note in notes:
            highlights = {}
            if query:
                highlights["content"] = self._highlight_text(note.content, query)
            
            results.append({
                "id": note.id,
                "title": note.title,
                "highlights": highlights,
                "category": {
                    "id": note.category.id,
                    "name": note.category.name
                } if note.category else None,
                "score": self._calculate_score(note, query),
                "created_at": note.created_at
            })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    
    def _highlight_text(self, text: str, query: str) -> str:
        if not text or not query:
            return text
        
        import re
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return pattern.sub(f"<mark>{query}</mark>", text)
    
    def _calculate_score(self, note: Note, query: str) -> float:
        if not query:
            return 0.0
        
        score = 0.0
        query_lower = query.lower()
        
        if note.title and query_lower in note.title.lower():
            score += 2.0
        
        if note.content and query_lower in note.content.lower():
            score += 1.0
        
        keywords = note.get_keywords_list()
        for keyword in keywords:
            if query_lower in keyword.lower():
                score += 0.5
        
        return score
    
    def get_suggestions(self, partial: str, limit: int = 10) -> List[str]:
        if not partial or len(partial) < 2:
            return []
        
        notes = self.note_dao.get_recent(limit=100)
        suggestions = set()
        
        for note in notes:
            if note.title:
                words = note.title.split()
                for word in words:
                    if word.lower().startswith(partial.lower()):
                        suggestions.add(word)
            
            keywords = note.get_keywords_list()
            for keyword in keywords:
                if keyword.lower().startswith(partial.lower()):
                    suggestions.add(keyword)
        
        return list(suggestions)[:limit]
