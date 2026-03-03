from typing import List, Optional, Dict
import math
from collections import Counter
import jieba
import jieba.analyse
from sqlalchemy.orm import Session
from app.dao.category_dao import CategoryDAO
from app.models.category import Category
from app.utils.cilin import get_cilin

CORE_WEIGHT = 3.0
IMPORTANT_WEIGHT = 2.0
BASIC_WEIGHT = 1.0
SYNONYM_WEIGHT = 0.3
HIDDEN_WEIGHT = 0.5

LAYERED_KEYWORDS = {
    "物理": {
        "core": ["物理"],
        "important": ["力学", "电磁学", "光学", "热学", "声学", "原子物理", "电学", "磁学", "动力学", "静力学", "运动学"],
        "basic": ["运动", "静止", "参照物", "速度", "加速度", "力", "质量", "密度", "体积", "功", "功率", "温度", "热量", "电流", "电压", "电阻", "透镜", "成像", "机械运动", "相对运动", "位移", "路程", "时间", "速率", "重力", "弹力", "摩擦力", "浮力", "压力", "杠杆", "滑轮", "斜面", "内能", "比热容", "反射", "折射", "焦距", "物距", "像距", "实像", "虚像", "电路", "串联", "并联", "能量", "动能", "势能", "机械能", "守恒", "振动", "波", "声", "光", "电", "磁"],
    },
    "数学": {
        "core": ["数学"],
        "important": ["代数", "几何", "三角", "概率", "统计", "微积分", "线性代数", "解析几何", "立体几何"],
        "basic": ["函数", "方程", "定理", "证明", "积分", "微分", "数列", "极限", "导数", "矩阵", "向量", "复数", "圆锥曲线", "椭圆", "双曲线", "抛物线", "不等式", "集合", "逻辑", "命题", "排列", "组合", "二项式", "多项式", "因式分解", "平方根", "对数", "指数", "三角函数", "正弦", "余弦", "正切", "坐标", "斜率", "距离", "角度", "面积", "体积"],
    },
    "化学": {
        "core": ["化学"],
        "important": ["有机化学", "无机化学", "物理化学", "分析化学", "生物化学"],
        "basic": ["分子", "原子", "元素", "反应", "溶液", "酸", "碱", "盐", "氧化", "还原", "化学式", "化合物", "电子", "质子", "中子", "官能团", "烃", "醇", "醛", "酮", "酯", "苯", "烷", "烯", "炔", "摩尔", "物质的量", "浓度", "溶解度", "电离", "水解", "原电池", "电解池", "金属", "非金属", "周期表", "离子", "键", "化学键", "共价键", "离子键"],
    },
    "英语": {
        "core": ["English", "英语"],
        "important": ["grammar", "vocabulary", "语法", "词汇", "reading", "writing", "listening", "speaking"],
        "basic": ["单词", "verb", "noun", "adjective", "tense", "sentence", "翻译", "阅读", "听力", "口语", "写作", "pronunciation", "phrase", "clause", "preposition", "conjunction", "article", "plural", "singular", "passive", "active", "conditional", "modal", "infinitive", "gerund", "participle", "subject", "object", "predicate", "adverb", "pronoun"],
    },
    "编程": {
        "core": ["编程", "程序设计"],
        "important": ["算法", "数据结构", "前端", "后端", "数据库", "架构", "软件工程"],
        "basic": ["代码", "函数", "变量", "循环", "条件", "数组", "对象", "类", "API", "HTTP", "Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript", "React", "Vue", "Node", "Docker", "Git", "Linux", "SQL", "NoSQL", "REST", "GraphQL", "微服务", "设计模式", "测试", "调试", "性能", "安全", "接口", "框架", "库", "模块", "包", "继承", "多态", "封装"],
    },
    "语文": {
        "core": ["语文", "汉语"],
        "important": ["作文", "阅读理解", "文言文", "古诗词", "文学", "修辞"],
        "basic": ["诗歌", "散文", "小说", "比喻", "拟人", "夸张", "排比", "对偶", "成语", "病句", "标点", "拼音", "汉字", "词语", "句子", "段落", "篇章", "作家", "作品", "朝代", "唐诗", "宋词", "元曲", "名著", "记叙", "说明", "议论", "抒情", "描写", "主语", "谓语", "宾语", "定语", "状语"],
    },
    "历史": {
        "core": ["历史"],
        "important": ["中国史", "世界史", "古代史", "近代史", "现代史", "政治史", "经济史", "文化史"],
        "basic": ["朝代", "皇帝", "战争", "革命", "改革", "条约", "政权", "民族", "文化", "经济", "政治", "外交", "军事", "秦", "汉", "唐", "宋", "元", "明", "清", "民国", "建国", "改革开放", "工业革命", "文艺复兴", "启蒙运动", "法国大革命", "美国独立", "俄国革命", "两次世界大战", "冷战", "殖民地", "封建", "资本主义", "社会主义"],
    },
    "地理": {
        "core": ["地理"],
        "important": ["自然地理", "人文地理", "经济地理", "区域地理", "地图学"],
        "basic": ["地图", "地形", "气候", "水文", "土壤", "植被", "人口", "城市", "农业", "工业", "交通", "贸易", "资源", "环境", "生态", "经纬度", "时区", "季风", "洋流", "板块", "地震", "火山", "河流", "湖泊", "海洋", "山脉", "平原", "高原", "盆地", "丘陵", "沙漠", "冰川", "可持续发展", "区域", "国家", "省份", "经度", "纬度", "海拔"],
    },
    "生物": {
        "core": ["生物", "生物学"],
        "important": ["细胞生物学", "遗传学", "生态学", "分子生物学", "微生物学", "植物学", "动物学"],
        "basic": ["细胞", "基因", "DNA", "RNA", "蛋白质", "酶", "新陈代谢", "呼吸", "光合作用", "遗传", "变异", "进化", "生态", "物种", "种群", "群落", "生态系统", "生物圈", "微生物", "植物", "动物", "人体", "器官", "组织", "系统", "神经", "激素", "免疫", "繁殖", "发育", "生长", "健康", "疾病", "营养", "染色体", "核酸", "氨基酸"],
    },
    "政治": {
        "core": ["政治"],
        "important": ["政治学", "经济学", "哲学", "法学", "国际政治"],
        "basic": ["国家", "政府", "政党", "民主", "法治", "宪法", "法律", "权利", "义务", "公民", "选举", "决策", "管理", "监督", "经济制度", "所有制", "市场", "宏观调控", "财政", "税收", "货币", "银行", "保险", "证券", "国际关系", "外交", "联合国", "欧盟", "东盟", "一带一路", "人类命运共同体", "人民代表大会", "政协", "国务院"],
    },
}


class ClassifyService:
    def __init__(self, db: Session):
        self.category_dao = CategoryDAO(db)
        self._keyword_cache: Dict[int, Dict[str, float]] = {}
        self._layered_cache: Dict[str, Dict[str, Dict[str, float]]] = {}
    
    def _get_layered_keywords(self, category_name: str) -> Dict[str, Dict[str, float]]:
        if category_name in self._layered_cache:
            return self._layered_cache[category_name]
        
        if category_name not in LAYERED_KEYWORDS:
            return {}
        
        result = {"core": {}, "important": {}, "basic": {}, "synonym": {}}
        layers = LAYERED_KEYWORDS[category_name]
        cilin = get_cilin()
        
        for kw in layers.get("core", []):
            result["core"][kw.lower()] = CORE_WEIGHT
        
        for kw in layers.get("important", []):
            result["important"][kw.lower()] = IMPORTANT_WEIGHT
        
        for kw in layers.get("basic", []):
            result["basic"][kw.lower()] = BASIC_WEIGHT
        
        all_keywords = layers.get("core", []) + layers.get("important", []) + layers.get("basic", [])
        for kw in all_keywords:
            synonyms = cilin.get_synonyms(kw)
            for syn in synonyms[:5]:
                syn_lower = syn.lower()
                if syn_lower not in result["core"] and syn_lower not in result["important"] and syn_lower not in result["basic"]:
                    if syn_lower not in result["synonym"]:
                        result["synonym"][syn_lower] = SYNONYM_WEIGHT
        
        self._layered_cache[category_name] = result
        return result
    
    def _extract_hidden_keywords(self, content: str, top_k: int = 20) -> List[str]:
        if not content:
            return []
        
        try:
            keywords = jieba.analyse.extract_tags(
                content,
                topK=top_k * 2,
                withWeight=True,
                allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'eng')
            )
            
            stopwords = {"的", "是", "在", "了", "和", "与", "或", "等", "及", "也", "有", "这", "那", "之", "为", "以", "于", "上", "下", "中", "来", "去", "到", "从", "向", "把", "被", "将", "能", "会", "可以", "可能", "应该", "必须", "要", "得", "着", "过", "地", "就", "才", "还", "又", "再", "都", "很", "太", "更", "最", "个", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "第", "其", "此", "每", "各", "某", "所", "些"}
            
            filtered = []
            for kw, weight in keywords:
                if kw.lower() not in stopwords and len(kw) > 1:
                    filtered.append(kw.lower())
                    if len(filtered) >= top_k:
                        break
            
            return filtered
        except Exception:
            return []
    
    def _calculate_weighted_score(self, content: str, hidden_keywords: List[str], category: Category) -> float:
        if not category:
            return 0.0
        
        layered = self._get_layered_keywords(category.name)
        if not layered:
            return 0.0
        
        content_lower = content.lower()
        total_score = 0.0
        max_possible = 0.0
        
        for layer_name, keywords in layered.items():
            layer_weight = {
                "core": CORE_WEIGHT,
                "important": IMPORTANT_WEIGHT,
                "basic": BASIC_WEIGHT,
                "synonym": SYNONYM_WEIGHT
            }.get(layer_name, 1.0)
            
            for kw, weight in keywords.items():
                max_possible += weight
                if kw in content_lower:
                    total_score += weight
        
        for kw in hidden_keywords:
            max_possible += HIDDEN_WEIGHT
            for layer_name, keywords in layered.items():
                if kw in keywords:
                    total_score += HIDDEN_WEIGHT
                    break
        
        return total_score / max_possible if max_possible > 0 else 0.0
    
    def classify(self, content: str) -> Optional[Category]:
        if not content:
            return None
        
        categories = self.category_dao.get_all()
        if not categories:
            return None
        
        hidden_keywords = self._extract_hidden_keywords(content, 20)
        
        scores = []
        for category in categories:
            score = self._calculate_weighted_score(content, hidden_keywords, category)
            scores.append((category, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        if scores and scores[0][1] > 0:
            return scores[0][0]
        
        default = self.category_dao.get_by_name("其他")
        return default
    
    def get_top_categories(self, content: str, top_k: int = 3) -> List[tuple]:
        if not content:
            return []

        categories = self.category_dao.get_all()
        if not categories:
            return []

        hidden_keywords = self._extract_hidden_keywords(content, 20)

        scores = []
        for category in categories:
            score = self._calculate_weighted_score(content, hidden_keywords, category)
            if score > 0:
                scores.append((category, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
