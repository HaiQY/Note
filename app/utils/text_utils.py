import re
import string
from typing import List

def clean_text(text: str) -> str:
    if not text:
        return ""
    
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    text = text.strip()
    
    return text

def extract_preview(text: str, max_length: int = 100) -> str:
    if not text:
        return ""
    
    cleaned = clean_text(text)
    if len(cleaned) <= max_length:
        return cleaned
    
    return cleaned[:max_length] + "..."

def remove_punctuation(text: str) -> str:
    translator = str.maketrans('', '', string.punctuation + '，。！？、；：""''（）【】')
    return text.translate(translator)

def count_words(text: str) -> int:
    if not text:
        return 0
    
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    
    return chinese_chars + english_words

def highlight_keywords(text: str, keywords: List[str], tag: str = "mark") -> str:
    if not keywords:
        return text
    
    for keyword in keywords:
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        text = pattern.sub(f'<{tag}>{keyword}</{tag}>', text)
    
    return text
