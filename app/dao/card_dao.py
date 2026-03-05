from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.card import ReviewCard, ReviewLog
import math

SM2_EF_MIN = 1.3
SM2_EF_INCREMENT_BASE = 0.1
SM2_EF_PENALTY_FACTOR = 0.08
SM2_EF_PENALTY_MULTIPLIER = 0.02

class CardDAO:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, note_id: int = None, is_active: bool = None,
                skip: int = 0, limit: int = 20) -> tuple[List[ReviewCard], int]:
        query = self.db.query(ReviewCard)
        
        if note_id:
            query = query.filter(ReviewCard.note_id == note_id)
        if is_active is not None:
            query = query.filter(ReviewCard.is_active == is_active)
        
        total = query.count()
        cards = query.order_by(ReviewCard.created_at.desc()).offset(skip).limit(limit).all()
        return cards, total
    
    def get_by_id(self, card_id: int) -> Optional[ReviewCard]:
        return self.db.query(ReviewCard).filter(ReviewCard.id == card_id).first()
    
    def create(self, note_id: int, question: str, answer: str,
               card_type: str = "qa", difficulty: int = 3) -> ReviewCard:
        card = ReviewCard(
            note_id=note_id,
            question=question,
            answer=answer,
            card_type=card_type,
            difficulty=difficulty,
            next_review=datetime.now()
        )
        self.db.add(card)
        self.db.commit()
        self.db.refresh(card)
        return card
    
    def create_batch(self, cards_data: List[dict]) -> List[ReviewCard]:
        cards = []
        for card_data in cards_data:
            card = ReviewCard(
                note_id=card_data["note_id"],
                question=card_data["question"],
                answer=card_data["answer"],
                card_type=card_data.get("card_type", "qa"),
                difficulty=card_data.get("difficulty", 3),
                next_review=datetime.now()
            )
            cards.append(card)
            self.db.add(card)
        self.db.commit()
        for card in cards:
            self.db.refresh(card)
        return cards
    
    def update(self, card_id: int, **kwargs) -> Optional[ReviewCard]:
        card = self.get_by_id(card_id)
        if not card:
            return None
        for key, value in kwargs.items():
            if hasattr(card, key):
                setattr(card, key, value)
        card.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(card)
        return card
    
    def delete(self, card_id: int) -> bool:
        card = self.get_by_id(card_id)
        if not card:
            return False
        self.db.delete(card)
        self.db.commit()
        return True
    
    def get_for_review(self, limit: int = 20) -> List[ReviewCard]:
        now = datetime.now()
        return self.db.query(ReviewCard).filter(
            ReviewCard.is_active == True,
            (ReviewCard.next_review == None) | (ReviewCard.next_review <= now)
        ).order_by(ReviewCard.next_review.asc()).limit(limit).all()
    
    def submit_review(self, card_id: int, quality: int, time_spent: int = None) -> Optional[dict]:
        card = self.get_by_id(card_id)
        if not card:
            return None
        
        old_interval = card.interval
        old_ease_factor = card.ease_factor
        
        if quality >= 3:
            if card.review_count == 0:
                card.interval = 1
            elif card.review_count == 1:
                card.interval = 3
            else:
                card.interval = math.ceil(old_interval * old_ease_factor)
            
            card.ease_factor = max(SM2_EF_MIN, old_ease_factor + (SM2_EF_INCREMENT_BASE - (5 - quality) * (SM2_EF_PENALTY_FACTOR + (5 - quality) * SM2_EF_PENALTY_MULTIPLIER)))
            card.correct_count += 1
        else:
            card.interval = 1
            card.review_count = 0
        
        card.review_count += 1
        card.next_review = datetime.now() + timedelta(days=card.interval)
        card.last_review = datetime.now()
        
        review_log = ReviewLog(
            card_id=card_id,
            quality=quality,
            time_spent=time_spent
        )
        self.db.add(review_log)
        
        self.db.commit()
        self.db.refresh(card)
        
        return {
            "card_id": card.id,
            "next_review": card.next_review,
            "interval": card.interval,
            "ease_factor": card.ease_factor,
            "review_count": card.review_count
        }
    
    def get_by_note(self, note_id: int) -> List[ReviewCard]:
        return self.db.query(ReviewCard).filter(ReviewCard.note_id == note_id).all()
