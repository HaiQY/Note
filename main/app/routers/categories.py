from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import ResponseBase, CategoryCreate, CategoryUpdate, CategoryResponse
from app.dao import CategoryDAO

router = APIRouter(prefix="/api/categories", tags=["categories"])

@router.get("", response_model=ResponseBase)
def get_categories(db: Session = Depends(get_db)):
    category_dao = CategoryDAO(db)
    categories = category_dao.get_all()
    
    items = []
    for cat in categories:
        items.append({
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "keywords": cat.get_keywords_list(),
            "color": cat.color,
            "icon": cat.icon,
            "sort_order": cat.sort_order,
            "created_at": cat.created_at.isoformat(),
            "updated_at": cat.updated_at.isoformat()
        })
    
    return ResponseBase(code=200, message="success", data=items)

@router.post("", response_model=ResponseBase)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    category_dao = CategoryDAO(db)
    
    existing = category_dao.get_by_name(category.name)
    if existing:
        raise HTTPException(status_code=400, detail="分类名称已存在")
    
    new_category = category_dao.create(
        name=category.name,
        description=category.description,
        keywords=category.keywords,
        color=category.color,
        icon=category.icon
    )
    
    return ResponseBase(
        code=200,
        message="创建成功",
        data={
            "id": new_category.id,
            "name": new_category.name,
            "color": new_category.color
        }
    )

@router.put("/{category_id}", response_model=ResponseBase)
def update_category(category_id: int, category_update: CategoryUpdate, db: Session = Depends(get_db)):
    category_dao = CategoryDAO(db)
    
    existing = category_dao.get_by_id(category_id)
    if not existing:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    update_data = category_update.model_dump(exclude_unset=True)
    updated = category_dao.update(category_id, **update_data)
    
    return ResponseBase(
        code=200,
        message="更新成功",
        data={
            "id": updated.id,
            "name": updated.name
        }
    )

@router.delete("/{category_id}", response_model=ResponseBase)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category_dao = CategoryDAO(db)
    
    if not category_dao.delete(category_id):
        raise HTTPException(status_code=404, detail="分类不存在")
    
    return ResponseBase(code=200, message="删除成功")
