from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.settings import Settings


class SettingsDAO:
    DEFAULT_SETTINGS = [
        {"key": "USE_STRUCTURE_V3", "value": "true", "description": "是否使用PaddleStructure V3模型进行OCR识别"},
        {"key": "AI_REFINE_OCR", "value": "false", "description": "是否使用AI整理OCR识别结果"},
    ]

    def __init__(self, db: Session):
        self.db = db

    def get(self, key: str) -> Optional[Settings]:
        return self.db.query(Settings).filter(Settings.key == key).first()

    def get_value(self, key: str, default: str = None) -> Optional[str]:
        setting = self.get(key)
        return setting.value if setting else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.get_value(key)
        if value is None:
            return default
        return value.lower() == "true"

    def set(self, key: str, value: str, description: str = None) -> Settings:
        setting = self.get(key)
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = Settings(key=key, value=value, description=description)
            self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting

    def set_bool(self, key: str, value: bool) -> Settings:
        return self.set(key, "true" if value else "false")

    def get_all(self) -> List[Settings]:
        return self.db.query(Settings).all()

    def init_defaults(self):
        for item in self.DEFAULT_SETTINGS:
            if not self.get(item["key"]):
                self.set(item["key"], item["value"], item["description"])