from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.schemas import ResponseBase
from app.services import SearchService

router = APIRouter(prefix="/api/search", tags=["search"])

@router.get("", response_model=ResponseBase)
def search(
    q: str = Query(..., min_length=1),
    category_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    search_service = SearchService(db)
    
    dt_from = None
    dt_to = None
    
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="开始日期格式应为 YYYY-MM-DD")
    
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d")
            dt_to = dt_to.replace(hour=23, minute=59, second=59)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束日期格式应为 YYYY-MM-DD")
    
    results = search_service.search(
        query=q,
        category_id=category_id,
        date_from=dt_from,
        date_to=dt_to,
        limit=limit
    )
    
    for item in results:
        if "created_at" in item and item["created_at"]:
            item["created_at"] = item["created_at"].isoformat()
    
    return ResponseBase(
        code=200,
        message="success",
        data={
            "items": results,
            "total": len(results),
            "query": q
        }
    )

@router.get("/suggestions", response_model=ResponseBase)
def get_suggestions(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    search_service = SearchService(db)
    suggestions = search_service.get_suggestions(q, limit)
    
    return ResponseBase(
        code=200,
        message="success",
        data=suggestions
    )
