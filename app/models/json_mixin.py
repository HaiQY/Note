import json
from typing import List, Dict, Any, Optional

class JSONColumnMixin:
    def get_json_list(self, column: str) -> List[str]:
        try:
            value: Optional[str] = getattr(self, column, None)
            return json.loads(value) if value else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_json_list(self, column: str, value: List[str]):
        setattr(self, column, json.dumps(value, ensure_ascii=False))
    
    def get_json_dict(self, column: str) -> Dict[str, Any]:
        try:
            value: Optional[str] = getattr(self, column, None)
            return json.loads(value) if value else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_json_dict(self, column: str, value: Dict[str, Any]):
        setattr(self, column, json.dumps(value, ensure_ascii=False))