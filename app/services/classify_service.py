from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.dao.category_dao import CategoryDAO
from app.models.category import Category
from app.utils.cilin import get_cilin

SYNONYM_WEIGHT = 0.6


class ClassifyService:
    def __init__(self, db: Session):
        self.category_dao = CategoryDAO(db)
        self._keyword_cache: Dict[int, Dict[str, float]] = {}
    
    def _get_expanded_keywords(self, category: Category) -> Dict[str, float]:
        if category.id in self._keyword_cache:
            return self._keyword_cache[category.id]
        
        keywords = category.get_keywords_list()
        if not keywords:
            self._keyword_cache[category.id] = {}
            return {}
        
        expanded = {}
        cilin = get_cilin()
        
        for keyword in keywords:
            expanded[keyword.lower()] = 1.0
            synonyms = cilin.get_synonyms(keyword)
            for syn in synonyms[:5]:
                syn_lower = syn.lower()
                if syn_lower not in expanded:
                    expanded[syn_lower] = SYNONYM_WEIGHT
        
        self._keyword_cache[category.id] = expanded
        return expanded
    
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
        
        expanded_keywords = self._get_expanded_keywords(category)
        if not expanded_keywords:
            return 0.0
        
        content_lower = content.lower()
        total_score = 0.0
        max_possible = len(expanded_keywords)
        
        for keyword, weight in expanded_keywords.items():
            if keyword in content_lower:
                total_score += weight

        return total_score / max_possible if max_possible > 0 else 0.0

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
