import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

APP_NAME = os.getenv("APP_NAME", "Note Organizer")
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-secret-key-change-in-production"
    else:
        raise ValueError("SECRET_KEY must be set in production")

DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
IMAGES_DIR = Path(os.getenv("IMAGES_DIR", DATA_DIR / "images"))
MARKDOWN_DIR = Path(os.getenv("MARKDOWN_DIR", DATA_DIR / "markdown"))
CARDS_DIR = Path(os.getenv("CARDS_DIR", DATA_DIR / "cards"))

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/notes.db")

OCR_LANG = os.getenv("OCR_LANG", "ch")

USE_STRUCTURE_V3 = os.getenv("USE_STRUCTURE_V3", "true").lower() == "true"
STRUCTURE_USE_FORMULA = os.getenv("STRUCTURE_USE_FORMULA", "true").lower() == "true"
STRUCTURE_USE_TABLE = os.getenv("STRUCTURE_USE_TABLE", "true").lower() == "true"
STRUCTURE_FORMULA_MODEL = os.getenv("STRUCTURE_FORMULA_MODEL", "PP-FormulaNet_plus-M")
STRUCTURE_DEVICE = os.getenv("STRUCTURE_DEVICE", "gpu")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")

AI_REFINE_OCR = os.getenv("AI_REFINE_OCR", "false").lower() == "true"

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

STOPWORDS_FILE = os.getenv("STOPWORDS_FILE", "")


def ensure_directories():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
    CARDS_DIR.mkdir(parents=True, exist_ok=True)


def validate_config():
    errors = []
    
    if DATABASE_URL:
        valid_schemes = ('sqlite:///', 'postgresql://', 'mysql://', 'mysql+pymysql://')
        if not any(DATABASE_URL.startswith(scheme) for scheme in valid_schemes):
            errors.append(f"DATABASE_URL 格式无效: {DATABASE_URL}")
    
    if not DEBUG:
        if SECRET_KEY == "dev-secret-key-change-in-production":
            errors.append("生产环境必须设置自定义 SECRET_KEY")
    
    if errors:
        from app.logger import logger
        for error in errors:
            logger.error(f"配置错误: {error}")
        if not DEBUG:
            raise ValueError("配置验证失败: " + "; ".join(errors))
    
    return True