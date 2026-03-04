import time
import numpy as np
from typing import List, Optional, Tuple, Dict
from threading import Lock
from sqlalchemy.orm import Session

from app.logger import logger
from app.models.category import Category
from app.dao.category_dao import CategoryDAO
from app.exp_service.config import (
    EMBEDDING_MODEL_NAME,
    EMBEDDING_DIM,
    EMBEDDING_MODEL_CACHE,
    HF_MIRROR,
    DEFAULT_THRESHOLD,
)
from app.exp_service.category_embeddings import CategoryEmbeddingManager


class EmbeddingClassifier:
    _instance = None
    _class_model = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if EmbeddingClassifier._class_model is None:
            self._init_model()
        
        self.embedding_manager = CategoryEmbeddingManager(self.encode)
        self._category_cache: Dict[int, Category] = {}
    
    def _init_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
            
            model_kwargs = {}
            if HF_MIRROR:
                logger.info(f"Using HuggingFace mirror: {HF_MIRROR}")
            
            EmbeddingClassifier._class_model = SentenceTransformer(
                EMBEDDING_MODEL_NAME,
                cache_folder=EMBEDDING_MODEL_CACHE if EMBEDDING_MODEL_CACHE else None
            )
            logger.info("Embedding model loaded successfully")
        except ImportError:
            logger.warning("sentence-transformers not installed. EmbeddingClassifier will return None.")
            EmbeddingClassifier._class_model = None
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}")
            logger.warning("You can try setting HF_MIRROR environment variable to a mirror site")
            logger.warning("Example: set HF_MIRROR=https://hf-mirror.com")
            EmbeddingClassifier._class_model = None
    
    @property
    def model(self):
        return EmbeddingClassifier._class_model
    
    def encode(self, text: str) -> np.ndarray:
        if self.model is None:
            return np.zeros(EMBEDDING_DIM)
        
        if not text or not text.strip():
            return np.zeros(EMBEDDING_DIM)
        
        try:
            embedding = self.model.encode(text, normalize_embeddings=True)
            return embedding
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            return np.zeros(EMBEDDING_DIM)
    
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        if self.model is None:
            return np.zeros((len(texts), EMBEDDING_DIM))
        
        try:
            embeddings = self.model.encode(texts, normalize_embeddings=True)
            return embeddings
        except Exception as e:
            logger.error(f"Batch encoding failed: {e}")
            return np.zeros((len(texts), EMBEDDING_DIM))
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def init_categories(self, db: Session) -> None:
        category_dao = CategoryDAO(db)
        categories = category_dao.get_all()
        
        self._category_cache = {cat.id: cat for cat in categories}
        self.embedding_manager.precompute_all(categories)
        logger.info(f"Initialized {len(categories)} categories for embedding classification")
    
    def classify(
        self, 
        content: str, 
        db: Session,
        threshold: float = DEFAULT_THRESHOLD
    ) -> Tuple[Optional[Category], float]:
        if self.model is None:
            logger.warning("Embedding model not available")
            return None, 0.0
        
        if not content or not content.strip():
            return None, 0.0
        
        if not self._category_cache:
            self.init_categories(db)
        
        content_embedding = self.encode(content)
        
        if np.all(content_embedding == 0):
            logger.warning("Content embedding is all zeros")
            return None, 0.0
        
        category_embeddings = self.embedding_manager.get_cached_embeddings()
        
        if not category_embeddings:
            logger.warning("No category embeddings in cache")
            return None, 0.0
        
        best_category: Optional[Category] = None
        best_score = -1.0
        all_scores = []
        
        for cat_id, cat_embedding in category_embeddings.items():
            if np.all(cat_embedding == 0):
                logger.debug(f"Category {cat_id} embedding is zeros")
                continue
            
            score = self._cosine_similarity(content_embedding, cat_embedding)
            cat_name = self._category_cache.get(cat_id)
            all_scores.append((cat_name.name if cat_name else str(cat_id), score))
            
            if score > best_score:
                best_score = score
                best_category = self._category_cache.get(cat_id)
        
        logger.debug(f"All scores: {sorted(all_scores, key=lambda x: x[1], reverse=True)[:5]}")
        logger.debug(f"Best score: {best_score}, threshold: {threshold}")
        
        if best_score < threshold:
            default_category = self._category_cache.get(
                next((k for k, v in self._category_cache.items() if v.name == "其他"), None)
            )
            return default_category, best_score
        
        return best_category, best_score
    
    def get_top_categories(
        self, 
        content: str, 
        db: Session,
        top_k: int = 3
    ) -> List[Tuple[Category, float]]:
        if self.model is None:
            return []
        
        if not content or not content.strip():
            return []
        
        if not self._category_cache:
            self.init_categories(db)
        
        content_embedding = self.encode(content)
        
        if np.all(content_embedding == 0):
            return []
        
        category_embeddings = self.embedding_manager.get_cached_embeddings()
        
        scores = []
        for cat_id, cat_embedding in category_embeddings.items():
            if np.all(cat_embedding == 0):
                continue
            
            score = self._cosine_similarity(content_embedding, cat_embedding)
            category = self._category_cache.get(cat_id)
            if category:
                scores.append((category, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def classify_with_timing(
        self, 
        content: str, 
        db: Session
    ) -> Tuple[Optional[Category], float, float]:
        start_time = time.perf_counter()
        category, score = self.classify(content, db)
        elapsed = time.perf_counter() - start_time
        return category, score, elapsed
    
    def is_available(self) -> bool:
        return self.model is not None