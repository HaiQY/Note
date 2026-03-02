from typing import List, Optional
from sqlalchemy.orm import Session
from app.dao.category_dao import CategoryDAO
from app.models.category import Category

class ClassifyService:
    def __init__(self, db: Session):
        self.category_dao = CategoryDAO(db)
    
    def classify(self, content: str) -> Optional[Category]:
        if not content:
            return None
        
        categories = self.category_dao.get_all()
        if not categories:
            return None
        
        scores = []
        for category in categories:
            score = self.calculate_similarity(content, category)
            scores.append((category, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        if scores and scores[0][1] > 0:
            return scores[0][0]
        
        default = self.category_dao.get_by_name("其他")
        return default
    
    def calculate_similarity(self, content: str, category: Category) -> float:
        if not content or not category:
            return 0.0
        
        keywords = category.get_keywords_list()
        if not keywords:
            return 0.0
        
        content_lower = content.lower()
        match_count = 0
        
        for keyword in keywords:
            if keyword.lower() in content_lower:
                match_count += 1
        
        if not keywords:
            return 0.0
        
        return match_count / len(keywords)
    
    def get_top_categories(self, content: str, top_k: int = 3) -> List[tuple]:
        if not content:
            return []
        
        categories = self.category_dao.get_all()
        if not categories:
            return []
        
        scores = []
        for category in categories:
            score = self.calculate_similarity(content, category)
            if score > 0:
                scores.append((category, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
