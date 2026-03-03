from pathlib import Path
from typing import List, Optional
import re

import jieba
import jieba.analyse

from app.config import STOPWORDS_FILE
from app.utils.text_utils import clean_text


class KeywordService:
    def __init__(self, stopwords_path: Optional[str] = None):
        self.stopwords = self._load_stopwords(stopwords_path or STOPWORDS_FILE)
        self._number_pattern = re.compile(r'^[\d\s\.\,\-\+\^\×\÷\=\<\>]+$')
        self._unit_pattern = re.compile(r'^[\d]+[\s]*[a-zA-Zμ°%]+$')
        self._chapter_pattern = re.compile(r'^[A-Za-z]+\d+$')
        self._mixed_pattern = re.compile(r'^[A-Za-z]+\d+[A-Za-z]*$')
    
    def _load_stopwords(self, filepath: Optional[str] = None) -> set:
        default_stopwords = {
            "的", "是", "在", "了", "和", "与", "或", "等", "及", "也",
            "有", "这", "那", "之", "为", "以", "于", "上", "下", "中",
            "来", "去", "到", "从", "向", "把", "被", "将", "能", "会",
            "可以", "可能", "应该", "必须", "要", "得", "着", "过", "地",
            "就", "才", "还", "又", "再", "都", "很", "太", "更", "最",
            "个", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
            "第", "其", "此", "每", "各", "某", "所", "些", "吗", "呢",
            "啊", "吧", "呀", "哦", "嗯", "哎", "唉", "喂", "嘿", "哈",
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "can",
            "and", "or", "but", "if", "then", "so", "because", "when",
            "where", "how", "what", "which", "who", "whom", "whose",
            "frac", "text", "eta", "quad", "cdot", "sqrt", "sum", "int",
            "lim", "alpha", "beta", "gamma", "delta", "theta", "lambda",
            "omega", "sigma", "phi", "psi", "rho", "mu", "pi", "infty",
            "rightarrow", "leftarrow", "Rightarrow", "Leftarrow",
            "mathrm", "mathbf", "italic", "underline",
            "mm", "cm", "km", "m", "nm", "μm", "pm",
            "kg", "g", "mg", "μg",
            "s", "min", "h", "hour", "second", "minute",
            "V", "A", "Ω", "W", "Hz", "kHz", "MHz",
            "Pa", "N", "J", "eV",
            "乘以", "除以", "等于", "小于", "大于", "约等于",
            "加", "减", "乘", "除", "等于", "取", "求", "得",
            "表示", "叫做", "称为", "是指", "定义为",
            "其中", "所以", "因此", "由于", "但是", "然而",
            "即", "则", "若", "如", "若", "使", "令",
            "等于", "约为", "接近", "大约", "左右", "上下",
            "ch", "section", "chapter",
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
            kw_str = str(kw)
            if kw not in self.stopwords and len(kw_str) > 1:
                if self._number_pattern.match(kw_str):
                    continue
                if self._unit_pattern.match(kw_str):
                    continue
                if re.search(r'[A-Za-z]+\d+', kw_str) and re.search(r'\d+[A-Za-z]+', kw_str):
                    continue
                if re.match(r'^[A-Za-z]+\d', kw_str):
                    continue
                if re.search(r'\d+[A-Za-z]+$', kw_str):
                    continue
                if len(kw_str) <= 2 and not re.search(r'[\u4e00-\u9fff]', kw_str):
                    continue
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