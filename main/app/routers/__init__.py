from fastapi import APIRouter
from app.routers import notes, categories, search, cards, ocr

router = APIRouter()

router.include_router(notes.router)
router.include_router(categories.router)
router.include_router(search.router)
router.include_router(cards.router)
router.include_router(ocr.router)
