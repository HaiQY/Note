from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.schemas import ResponseBase
from app.dao import SettingsDAO

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    key: str
    value: str


@router.get("", response_model=ResponseBase)
def get_all_settings(db: Session = Depends(get_db)):
    settings_dao = SettingsDAO(db)
    settings = settings_dao.get_all()
    
    items = []
    for s in settings:
        items.append({
            "key": s.key,
            "value": s.value,
            "description": s.description
        })
    
    return ResponseBase(
        code=200,
        message="success",
        data=items
    )


@router.get("/{key}", response_model=ResponseBase)
def get_setting(key: str, db: Session = Depends(get_db)):
    settings_dao = SettingsDAO(db)
    setting = settings_dao.get(key)
    
    if not setting:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return ResponseBase(
        code=200,
        message="success",
        data={
            "key": setting.key,
            "value": setting.value,
            "description": setting.description
        }
    )


@router.put("/{key}", response_model=ResponseBase)
def update_setting(key: str, data: SettingsUpdate, db: Session = Depends(get_db)):
    settings_dao = SettingsDAO(db)
    setting = settings_dao.set(key, data.value)
    
    return ResponseBase(
        code=200,
        message="设置已更新",
        data={
            "key": setting.key,
            "value": setting.value
        }
    )


@router.post("/boolean/{key}", response_model=ResponseBase)
def toggle_boolean_setting(key: str, value: bool = Query(...), db: Session = Depends(get_db)):
    settings_dao = SettingsDAO(db)
    setting = settings_dao.set_bool(key, value)
    
    return ResponseBase(
        code=200,
        message="设置已更新",
        data={
            "key": setting.key,
            "value": setting.value
        }
    )