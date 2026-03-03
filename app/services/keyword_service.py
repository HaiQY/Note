from pathlib import Path
from typing import List, Optional

import jieba
import jieba.analyse

from app.config import STOPWORDS_FILE
from app.utils.text_utils import clean_text


class KeywordService:
    def __init__(self, stopwords_path: Optional[str] = None):
        self.stopwords = self._load_stopwords(stopwords_path or STOPWORDS_FILE)
    
    def _load_stopwords(self, filepath: Optional[str] = None) -> set:
        default_stopwords = {
            "的", "是", "在", "了", "和", "与", "或", "等", "及", "也",
            "有", "这", "那", "之", "为", "以", "于", "上", "下", "中",
            "来", "去", "到", "从", "向", "把", "被", "将", "能", "会",
            "可以", "可能", "应该", "必须", "要", "得", "着", "过", "地",
            "就", "才", "还", "又", "再", "都", "很", "太", "更", "最",
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "can"
        }
        
        if filepath and Path(filepath).exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    custom_stopwords = set(line.strip() for line in f if line.strip())
                    return default_stopwords | custom_stopwords
            except Exception:
                pass
        
        return default_stopwords
    
    def extract_keywords(self, content: str, top_k: int = 5) -> List[str]:
        if not content:
            return []
        
        cleaned = clean_text(content)
        
        try:
            keywords = jieba.analyse.extract_tags(
                cleaned,
                topK=top_k * 2,
                withWeight=False,
                allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'eng')
            )
        except Exception:
            words = jieba.lcut(cleaned)
            keywords = [w for w in words if len(w) > 1 and w not in self.stopwords]
        
        filtered = []
        for kw in keywords:
            if kw not in self.stopwords and len(kw) > 1:
                filtered.append(kw)
                if len(filtered) >= top_k:
                    break
        
        return filtered
    
    def extract_keywords_textrank(self, content: str, top_k: int = 5) -> List[str]:
        if not content:
            return []
        
        cleaned = clean_text(content)
        
        try:
            keywords = jieba.analyse.textrank(
                cleaned,
                topK=top_k,
                withWeight=False,
                allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'eng')
            )
            return list(keywords)
        except Exception:
            return self.extract_keywords(content, top_k)
    
    def calculate_tfidf(self, content: str) -> dict:
        if not content:
            return {}
        
        cleaned = clean_text(content)
        
        try:
            keywords_with_weight = jieba.analyse.extract_tags(
                cleaned,
                topK=20,
                withWeight=True
            )
            return {kw: weight for kw, weight in keywords_with_weight}
        except Exception:
            return {}
    
    def add_user_word(self, word: str) -> None:
        jieba.add_word(word)
    
    def add_user_words(self, words: List[str]) -> None:
        for word in words:
            jieba.add_word(word)