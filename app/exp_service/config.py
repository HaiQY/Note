from pathlib import Path
from typing import Dict
import os

EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"

EMBEDDING_MODEL_CACHE = os.getenv(
    "EMBEDDING_MODEL_CACHE",
    str(Path.home() / ".cache" / "huggingface" / "hub")
)

HF_MIRROR = os.getenv("HF_MIRROR", "")

if HF_MIRROR:
    os.environ["HF_ENDPOINT"] = HF_MIRROR

EMBEDDING_DIM = 768
CACHE_DIR = Path("data/embedding_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CATEGORY_DESCRIPTIONS: Dict[str, str] = {
    "数学": "数学相关内容，包括代数、几何、微积分、概率统计、函数、方程、定理证明等数学学科知识",
    "物理": "物理学相关内容，包括力学、电磁学、光学、热学、原子物理等物理知识，涉及运动、力、能量、波等概念",
    "化学": "化学相关内容，包括有机化学、无机化学、化学反应、分子结构、元素周期表、化学键等化学知识",
    "英语": "英语学习相关内容，包括语法、词汇、阅读理解、写作、听力、口语等英语知识",
    "编程": "计算机编程相关内容，包括算法、数据结构、编程语言、软件开发、数据库、前端后端等技术知识",
    "语文": "语文相关内容，包括文学、作文、阅读理解、文言文、古诗词、修辞手法等汉语知识",
    "历史": "历史相关内容，包括中国历史、世界历史、朝代、历史事件、历史人物等历史知识",
    "地理": "地理相关内容，包括自然地理、人文地理、地图、气候、地形、区域地理等地理知识",
    "生物": "生物学相关内容，包括细胞、遗传、生态、进化、人体生理、植物动物等生物知识",
    "政治": "政治相关内容，包括政治制度、经济制度、哲学、法律、国际关系等政治知识",
    "其他": "不属于以上分类的其他内容",
}

DEFAULT_THRESHOLD = 0.1
TOP_KEYWORDS_FOR_DESCRIPTION = 10