from pathlib import Path
from typing import List, Dict, Optional
from functools import lru_cache
import threading

CILIN_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "dict" / "哈工大同义词词林" / "HIT-IRLab-同义词词林（扩展版）_full_2005.3.3.txt"


class CilinLoader:
    _instance = None
    _lock = threading.Lock()
    _loaded = False
    _word_to_synonyms: Dict[str, List[str]] = {}
    _word_to_group: Dict[str, str] = {}

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def _load(self):
        if self._loaded:
            return

        with self._lock:
            if self._loaded:
                return

            if not CILIN_FILE.exists():
                print(f"Warning: Cilin file not found: {CILIN_FILE}")
                self._loaded = True
                return

            try:
                with open(CILIN_FILE, "r", encoding="gbk") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        parts = line.split()
                        if len(parts) < 2:
                            continue

                        code = parts[0]
                        words = parts[1:]

                        marker = code[-1] if code else "="
                        if marker in ("=", "#"):
                            for word in words:
                                synonyms = [w for w in words if w != word]
                                if word not in self._word_to_synonyms:
                                    self._word_to_synonyms[word] = []
                                self._word_to_synonyms[word].extend(synonyms)

                for word in self._word_to_synonyms:
                    self._word_to_synonyms[word] = list(set(self._word_to_synonyms[word]))

                self._loaded = True
                print(f"Cilin loaded: {len(self._word_to_synonyms)} words")

            except Exception as e:
                print(f"Error loading Cilin: {e}")
                self._loaded = True

    def get_synonyms(self, word: str) -> List[str]:
        if not self._loaded:
            self._load()
        return self._word_to_synonyms.get(word, [])

    def get_synonyms_with_self(self, word: str) -> List[str]:
        synonyms = self.get_synonyms(word)
        return [word] + synonyms

    def is_synonym(self, word1: str, word2: str) -> bool:
        if word1 == word2:
            return True
        return word2 in self.get_synonyms(word1)

    def expand_words(self, words: List[str], max_synonyms: int = 3) -> Dict[str, List[str]]:
        result = {}
        for word in words:
            synonyms = self.get_synonyms(word)[:max_synonyms]
            result[word] = synonyms
        return result


_cilin_instance: Optional[CilinLoader] = None


def get_cilin() -> CilinLoader:
    global _cilin_instance
    if _cilin_instance is None:
        _cilin_instance = CilinLoader()
    return _cilin_instance


def get_synonyms(word: str) -> List[str]:
    return get_cilin().get_synonyms(word)


def expand_keywords(keywords: List[str], max_synonyms: int = 3) -> Dict[str, List[str]]:
    return get_cilin().expand_words(keywords, max_synonyms)