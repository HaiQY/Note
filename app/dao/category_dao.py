from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.category import Category

class CategoryDAO:
    DEFAULT_CATEGORIES = [
        {"name": "数学", "keywords": ["数学", "函数", "方程", "定理", "证明", "积分", "微分", "代数", "几何", "三角", "概率", "统计", "数列", "极限"], "color": "#e74c3c"},
        {"name": "物理", "keywords": ["物理", "力学", "电磁", "光学", "量子", "能量", "动量", "透镜", "凸透镜", "凹透镜", "成像", "光", "电", "磁", "力", "速度", "加速度", "质量", "功", "功率", "电路", "电阻", "电压", "电流", "牛顿", "焦耳"], "color": "#3498db"},
        {"name": "化学", "keywords": ["化学", "反应", "分子", "原子", "有机", "无机", "化学式", "元素", "化合物", "溶液", "酸", "碱", "盐", "氧化", "还原", "电解", "离子", "键"], "color": "#2ecc71"},
        {"name": "英语", "keywords": ["English", "英语", "grammar", "vocabulary", "单词", "语法", "verb", "noun", "adjective", "tense", "sentence", "翻译", "阅读", "听力"], "color": "#f39c12"},
        {"name": "编程", "keywords": ["编程", "代码", "算法", "数据结构", "Python", "JavaScript", "函数", "变量", "循环", "条件", "数组", "对象", "类", "API", "HTTP", "数据库", "前端", "后端"], "color": "#9b59b6"},
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
