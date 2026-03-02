from typing import List, Optional, Tuple
from pathlib import Path
import numpy as np
from app.config import OCR_LANG

class OCRResult:
    def __init__(self, text: str, confidence: float, boxes: List[List[int]] = None):
        self.text = text
        self.confidence = confidence
        self.boxes = boxes or []

class OCRService:
    _instance = None
    _ocr = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if OCRService._ocr is None:
            self._init_ocr()
    
    def _init_ocr(self):
        try:
            from paddleocr import PaddleOCR
            
            kwargs = {
                "use_angle_cls": True,
                "lang": OCR_LANG,
            }
            
            OCRService._ocr = PaddleOCR(**kwargs)
                
        except ImportError:
            print("Warning: PaddleOCR not installed. OCR service will return mock data.")
            OCRService._ocr = None
        except Exception as e:
            print(f"Warning: Failed to initialize PaddleOCR: {e}")
            OCRService._ocr = None
    
    def process_image(self, image_path: str) -> OCRResult:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        if OCRService._ocr is None:
            return self._mock_result(image_path)
        
        try:
            result = OCRService._ocr.ocr(str(path))
            
            if not result:
                return OCRResult(text="", confidence=0.0)
            
            texts = []
            confidences = []
            boxes = []
            
            if isinstance(result, dict):
                if 'rec_text' in result:
                    return OCRResult(text=result.get('rec_text', ''), confidence=result.get('rec_score', 0.9))
                if 'dt_polys' in result and 'rec_text' in result:
                    text = result.get('rec_text', '')
                    score = result.get('rec_score', 0.9)
                    return OCRResult(text=text, confidence=score)
            
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        if 'rec_texts' in item:
                            texts.extend(item.get('rec_texts', []))
                            scores = item.get('rec_scores', [])
                            if scores:
                                confidences.extend(scores)
                        elif 'rec_text' in item:
                            texts.append(item.get('rec_text', ''))
                            if 'rec_score' in item:
                                confidences.append(item.get('rec_score', 0.9))
                    elif isinstance(item, list):
                        for line in item:
                            if isinstance(line, dict) and 'rec_text' in line:
                                texts.append(line.get('rec_text', ''))
                                if 'rec_score' in line:
                                    confidences.append(line.get('rec_score', 0.9))
                            elif isinstance(line, (list, tuple)) and len(line) >= 2:
                                box = line[0]
                                text_info = line[1]
                                if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                                    texts.append(str(text_info[0]))
                                    confidences.append(float(text_info[1]))
                                elif isinstance(text_info, dict):
                                    texts.append(text_info.get('text', ''))
                                    confidences.append(text_info.get('confidence', 0.9))
            
            if not texts:
                return OCRResult(text=str(result), confidence=0.9)
            
            full_text = "\n".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.9
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                boxes=boxes
            )
        except Exception as e:
            raise RuntimeError(f"OCR processing failed: {e}")
    
    def process_image_bytes(self, image_bytes: bytes) -> OCRResult:
        if OCRService._ocr is None:
            return OCRResult(text="[模拟OCR结果] 这是一段测试文本，用于演示OCR功能。", confidence=0.95)
        
        try:
            import cv2
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            result = OCRService._ocr.ocr(img)
            
            if not result:
                return OCRResult(text="", confidence=0.0)
            
            texts = []
            confidences = []
            
            if isinstance(result, dict):
                if 'rec_text' in result:
                    return OCRResult(text=result.get('rec_text', ''), confidence=result.get('rec_score', 0.9))
            
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        if 'rec_texts' in item:
                            texts.extend(item.get('rec_texts', []))
                            scores = item.get('rec_scores', [])
                            if scores:
                                confidences.extend(scores)
                        elif 'rec_text' in item:
                            texts.append(item.get('rec_text', ''))
                            if 'rec_score' in item:
                                confidences.append(item.get('rec_score', 0.9))
                    elif isinstance(item, list):
                        for line in item:
                            if isinstance(line, dict) and 'rec_text' in line:
                                texts.append(line.get('rec_text', ''))
                                if 'rec_score' in line:
                                    confidences.append(line.get('rec_score', 0.9))
                            elif isinstance(line, (list, tuple)) and len(line) >= 2:
                                text_info = line[1]
                                if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                                    texts.append(str(text_info[0]))
                                    confidences.append(float(text_info[1]))
            
            if not texts:
                return OCRResult(text=str(result), confidence=0.9)
            
            full_text = "\n".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.9
            
            return OCRResult(text=full_text, confidence=avg_confidence)
        except Exception as e:
            raise RuntimeError(f"OCR processing failed: {e}")
    
    def batch_process(self, image_paths: List[str]) -> List[OCRResult]:
        results = []
        for path in image_paths:
            try:
                results.append(self.process_image(path))
            except Exception as e:
                results.append(OCRResult(text="", confidence=0.0))
        return results
    
    def _mock_result(self, image_path: str) -> OCRResult:
        mock_text = f"[模拟OCR结果] 图片 {Path(image_path).name} 的识别内容。\n这是一段测试文本，用于演示OCR功能。\n支持中文和English混合内容。"
        return OCRResult(text=mock_text, confidence=0.95)
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        return image
