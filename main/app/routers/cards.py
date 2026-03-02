from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import ResponseBase, CardCreate, CardUpdate, CardResponse, CardGenerateRequest, CardReviewRequest, CardReviewResponse
from app.dao import CardDAO, NoteDAO
from app.services import AIService

router = APIRouter(prefix="/api/cards", tags=["cards"])

@router.post("/generate/{note_id}", response_model=ResponseBase)
async def generate_cards(note_id: int, request: CardGenerateRequest, db: Session = Depends(get_db)):
    note_dao = NoteDAO(db)
    note = note_dao.get_by_id(note_id)
    
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    ai_service = AIService()
    cards_data = await ai_service.generate_cards(
        content=note.content,
        card_count=request.count,
        card_types=request.card_types
    )
    
    card_dao = CardDAO(db)
    created_cards = []
    
    for card_data in cards_data:
        card_data["note_id"] = note_id
        card = card_dao.create(
            note_id=note_id,
            question=card_data["question"],
            answer=card_data["answer"],
            card_type=card_data.get("card_type", "qa"),
            difficulty=card_data.get("difficulty", 3)
        )
        created_cards.append({
            "id": card.id,
            "question": card.question,
            "answer": card.answer,
            "card_type": card.card_type,
            "difficulty": card.difficulty
        })
    
    return ResponseBase(
        code=200,
        message=f"成功生成 {len(created_cards)} 张卡片",
        data={
            "generated_count": len(created_cards),
            "cards": created_cards
        }
    )

@router.get("", response_model=ResponseBase)
def get_cards(
    note_id: int = None,
    is_active: bool = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    card_dao = CardDAO(db)
    skip = (page - 1) * page_size
    
    cards, total = card_dao.get_all(
        note_id=note_id,
        is_active=is_active,
        skip=skip,
        limit=page_size
    )
    
    items = []
    for card in cards:
        items.append({
            "id": card.id,
            "note_id": card.note_id,
            "question": card.question,
            "answer": card.answer,
            "card_type": card.card_type,
            "difficulty": card.difficulty,
            "next_review": card.next_review.isoformat() if card.next_review else None,
            "interval": card.interval,
            "ease_factor": card.ease_factor,
            "review_count": card.review_count,
            "correct_count": card.correct_count,
            "is_active": card.is_active,
            "created_at": card.created_at.isoformat()
        })
    
    total_pages = (total + page_size - 1) // page_size
    
    return ResponseBase(
        code=200,
        message="success",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    )

@router.get("/review", response_model=ResponseBase)
def get_cards_for_review(limit: int = 20, db: Session = Depends(get_db)):
    """获取待复习的卡片列表"""
    card_dao = CardDAO(db)
    cards = card_dao.get_for_review(limit)
    
    items = []
    for card in cards:
        items.append({
            "id": card.id,
            "note_id": card.note_id,
            "question": card.question,
            "answer": card.answer,
            "card_type": card.card_type,
            "difficulty": card.difficulty,
            "next_review": card.next_review.isoformat() if card.next_review else None,
            "review_count": card.review_count
        })
    
    return ResponseBase(
        code=200,
        message="success",
        data={
            "items": items,
            "count": len(items)
        }
    )

@router.get("/{card_id}", response_model=ResponseBase)
def get_card(card_id: int, db: Session = Depends(get_db)):
    """获取单个卡片详情"""
    card_dao = CardDAO(db)
    card = card_dao.get_by_id(card_id)
    
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")
    
    return ResponseBase(
        code=200,
        message="success",
        data={
            "id": card.id,
            "note_id": card.note_id,
            "question": card.question,
            "answer": card.answer,
            "card_type": card.card_type,
            "difficulty": card.difficulty,
            "next_review": card.next_review.isoformat() if card.next_review else None,
            "interval": card.interval,
            "ease_factor": card.ease_factor,
            "review_count": card.review_count,
            "correct_count": card.correct_count,
            "last_review": card.last_review.isoformat() if card.last_review else None,
            "is_active": card.is_active,
            "created_at": card.created_at.isoformat(),
            "updated_at": card.updated_at.isoformat()
        }
    )

@router.post("/{card_id}/review", response_model=ResponseBase)
def submit_review(card_id: int, review: CardReviewRequest, db: Session = Depends(get_db)):
    card_dao = CardDAO(db)
    card = card_dao.get_by_id(card_id)
    
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")
    
    if not 0 <= review.quality <= 5:
        raise HTTPException(status_code=400, detail="quality 必须在 0-5 之间")
    
    result = card_dao.submit_review(card_id, review.quality, review.time_spent)
    
    return ResponseBase(
        code=200,
        message="复习记录已提交",
        data={
            "card_id": result["card_id"],
            "next_review": result["next_review"].isoformat(),
            "interval": result["interval"],
            "ease_factor": result["ease_factor"],
            "review_count": result["review_count"]
        }
    )

@router.put("/{card_id}", response_model=ResponseBase)
def update_card(card_id: int, card_update: CardUpdate, db: Session = Depends(get_db)):
    card_dao = CardDAO(db)
    card = card_dao.get_by_id(card_id)
    
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")
    
    update_data = card_update.model_dump(exclude_unset=True)
    updated = card_dao.update(card_id, **update_data)
    
    return ResponseBase(
        code=200,
        message="更新成功",
        data={
            "id": updated.id,
            "question": updated.question
        }
    )

@router.delete("/{card_id}", response_model=ResponseBase)
def delete_card(card_id: int, db: Session = Depends(get_db)):
    card_dao = CardDAO(db)
    
    if not card_dao.delete(card_id):
        raise HTTPException(status_code=404, detail="卡片不存在")
    
    return ResponseBase(code=200, message="删除成功")
