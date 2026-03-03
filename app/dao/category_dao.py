from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.category import Category

class CategoryDAO:
    DEFAULT_CATEGORIES = [
        {"name": "数学", "keywords": ["数学", "函数", "方程", "定理", "证明", "积分", "微分", "代数", "几何", "三角", "概率", "统计", "数列", "极限", "导数", "矩阵", "向量", "复数", "圆锥曲线", "椭圆", "双曲线", "抛物线"], "color": "#e74c3c"},
        {"name": "物理", "keywords": ["物理", "力学", "电磁", "光学", "量子", "能量", "动量", "透镜", "凸透镜", "凹透镜", "成像", "光", "电", "磁", "力", "速度", "加速度", "质量", "功", "功率", "电路", "电阻", "电压", "电流", "牛顿", "焦耳", "摩擦力", "重力", "弹力", "压强", "浮力", "杠杆", "滑轮", "斜面", "振动", "波", "声", "热", "温度", "热量", "比热容", "内能", "熵", "反射", "折射", "干涉", "衍射", "偏振", "电场", "磁场", "电磁波", "感应", "原子", "核", "衰变", "裂变", "聚变"], "color": "#3498db"},
        {"name": "化学", "keywords": ["化学", "反应", "分子", "原子", "有机", "无机", "化学式", "元素", "化合物", "溶液", "酸", "碱", "盐", "氧化", "还原", "电解", "离子", "键", "周期表", "电子", "质子", "中子", "官能团", "烃", "醇", "醛", "酮", "酸", "酯", "苯", "烷", "烯", "炔", "摩尔", "物质的量", "浓度", "溶解度", "电离", "水解", "原电池", "电解池", "金属", "非金属"], "color": "#2ecc71"},
        {"name": "英语", "keywords": ["English", "英语", "grammar", "vocabulary", "单词", "语法", "verb", "noun", "adjective", "tense", "sentence", "翻译", "阅读", "听力", "口语", "写作", "pronunciation", "phrase", "clause", "preposition", "conjunction", "article", "plural", "singular", "passive", "active", "conditional", "modal", "infinitive", "gerund", "participle"], "color": "#f39c12"},
        {"name": "编程", "keywords": ["编程", "代码", "算法", "数据结构", "Python", "JavaScript", "函数", "变量", "循环", "条件", "数组", "对象", "类", "API", "HTTP", "数据库", "前端", "后端", "Java", "C++", "Go", "Rust", "TypeScript", "React", "Vue", "Node", "Docker", "Git", "Linux", "SQL", "NoSQL", "REST", "GraphQL", "微服务", "架构", "设计模式", "测试", "调试", "性能", "安全"], "color": "#9b59b6"},
        {"name": "语文", "keywords": ["语文", "作文", "阅读理解", "文言文", "古诗词", "诗歌", "散文", "小说", "修辞", "比喻", "拟人", "夸张", "排比", "对偶", "成语", "病句", "标点", "拼音", "汉字", "词语", "句子", "段落", "篇章", "文学", "作家", "作品", "朝代", "唐诗", "宋词", "元曲", "名著"], "color": "#1abc9c"},
        {"name": "历史", "keywords": ["历史", "朝代", "皇帝", "战争", "革命", "改革", "条约", "政权", "民族", "文化", "经济", "政治", "外交", "军事", "古代", "近代", "现代", "中国史", "世界史", "秦", "汉", "唐", "宋", "元", "明", "清", "民国", "建国", "改革开放", "工业革命", "文艺复兴", "启蒙运动", "法国大革命", "美国独立", "俄国革命", "两次世界大战", "冷战"], "color": "#e67e22"},
        {"name": "地理", "keywords": ["地理", "地图", "地形", "气候", "水文", "土壤", "植被", "人口", "城市", "农业", "工业", "交通", "贸易", "资源", "环境", "生态", "经纬度", "时区", "季风", "洋流", "板块", "地震", "火山", "河流", "湖泊", "海洋", "山脉", "平原", "高原", "盆地", "丘陵", "沙漠", "冰川", "可持续发展", "区域", "国家", "省份"], "color": "#27ae60"},
        {"name": "生物", "keywords": ["生物", "细胞", "基因", "DNA", "RNA", "蛋白质", "酶", "新陈代谢", "呼吸", "光合作用", "遗传", "变异", "进化", "生态", "物种", "种群", "群落", "生态系统", "生物圈", "微生物", "植物", "动物", "人体", "器官", "组织", "系统", "神经", "激素", "免疫", "繁殖", "发育", "生长", "健康", "疾病", "营养"], "color": "#16a085"},
        {"name": "政治", "keywords": ["政治", "国家", "政府", "政党", "民主", "法治", "宪法", "法律", "权利", "义务", "公民", "选举", "决策", "管理", "监督", "经济制度", "所有制", "市场", "宏观调控", "财政", "税收", "货币", "银行", "保险", "证券", "国际关系", "外交", "联合国", "欧盟", "东盟", "一带一路", "人类命运共同体"], "color": "#c0392b"},
        {"name": "其他", "keywords": [], "color": "#95a5a6"},
    ]
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[Category]:
        return self.db.query(Category).order_by(Category.sort_order, Category.id).all()
    
    def get_by_id(self, category_id: int) -> Optional[Category]:
        return self.db.query(Category).filter(Category.id == category_id).first()
    
    def get_by_name(self, name: str) -> Optional[Category]:
        return self.db.query(Category).filter(Category.name == name).first()
    
    def create(self, name: str, description: str = None, keywords: List[str] = None, 
               color: str = "#3498db", icon: str = None) -> Category:
        category = Category(
            name=name,
            description=description,
            color=color,
            icon=icon
        )
        if keywords:
            category.set_keywords_list(keywords)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def update(self, category_id: int, **kwargs) -> Optional[Category]:
        category = self.get_by_id(category_id)
        if not category:
            return None
        for key, value in kwargs.items():
            if hasattr(category, key):
                if key == "keywords" and isinstance(value, list):
                    category.set_keywords_list(value)
                else:
                    setattr(category, key, value)
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def delete(self, category_id: int) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            return False
        self.db.delete(category)
        self.db.commit()
        return True
    
    def init_default_categories(self):
        import json
        for i, cat_data in enumerate(self.DEFAULT_CATEGORIES):
            if not self.get_by_name(cat_data["name"]):
                category = Category(
                    name=cat_data["name"],
                    keywords=json.dumps(cat_data["keywords"], ensure_ascii=False),
                    color=cat_data["color"],
                    sort_order=i
                )
                self.db.add(category)
        self.db.commit()
