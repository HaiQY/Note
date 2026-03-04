import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.category import Category
from app.exp_service.config import (
    CACHE_DIR,
    CATEGORY_DESCRIPTIONS,
    EMBEDDING_DIM,
)


class CategoryEmbeddingManager:
    def __init__(self, model_encode_func):
        self.encode = model_encode_func
        self._cache: Dict[int, np.ndarray] = {}
        self._cache_file = CACHE_DIR / "category_embeddings.json"
        self._vectors_file = CACHE_DIR / "category_vectors.npy"
    
    def build_category_text(self, category: Category) -> str:
        description = CATEGORY_DESCRIPTIONS.get(category.name, "")
        keywords = category.get_keywords_list() if hasattr(category, "get_keywords_list") else []
        
        parts = []
        if description:
            parts.append(f"分类：{category.name}。{description}")
        else:
            parts.append(f"分类：{category.name}。")
        
        if keywords:
            keywords_str = "、".join(keywords[:20])
            parts.append(f"相关关键词：{keywords_str}")
        
        return " ".join(parts)
    
    def _load_cache_from_disk(self) -> bool:
        if not self._cache_file.exists() or not self._vectors_file.exists():
            return False
        
        try:
            with open(self._cache_file, "r", encoding="utf-8") as f:
                cache_meta = json.load(f)
            
            vectors = np.load(self._vectors_file)
            
            for item in cache_meta:
                idx = item["index"]
                cat_id = item["category_id"]
                if idx < len(vectors):
                    self._cache[cat_id] = vectors[idx]
            
            return True
        except Exception:
            return False
    
    def _save_cache_to_disk(self):
        if not self._cache:
            return
        
        cache_meta = []
        vectors = []
        
        for idx, (cat_id, embedding) in enumerate(self._cache.items()):
            cache_meta.append({
                "index": idx,
                "category_id": cat_id,
            })
            vectors.append(embedding)
        
        with open(self._cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_meta, f, ensure_ascii=False, indent=2)
        
        np.save(self._vectors_file, np.array(vectors))
    
    def get_or_compute_embedding(self, category: Category) -> np.ndarray:
        if category.id in self._cache:
            return self._cache[category.id]
        
        text = self.build_category_text(category)
        embedding = self.encode(text)
        
        self._cache[category.id] = embedding
        self._save_cache_to_disk()
        
        return embedding
    
    def precompute_all(self, categories: List[Category]) -> Dict[int, np.ndarray]:
        self._load_cache_from_disk()
        
        for category in categories:
            if category.id not in self._cache:
                self.get_or_compute_embedding(category)
        
        self._save_cache_to_disk()
        return self._cache.copy()
    
    def clear_cache(self):
        self._cache.clear()
        if self._cache_file.exists():
            self._cache_file.unlink()
        if self._vectors_file.exists():
            self._vectors_file.unlink()
    
    def get_cached_embeddings(self) -> Dict[int, np.ndarray]:
        return self._cache.copy()