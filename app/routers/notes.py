from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pathlib import Path

from app.database import get_db
from app.schemas import ResponseBase, NoteResponse, NoteUpdate, NoteUploadResponse
from app.dao import NoteDAO, CategoryDAO
from app.services import OCRService, ClassifyService, KeywordService, MarkdownService, AIService
from app.utils import save_upload_file, validate_image, get_relative_path, extract_preview
from app.config import IMAGES_DIR, AI_REFINE_OCR

router = APIRouter(prefix="/api/notes", tags=["notes"])

@router.post("/upload", response_model=ResponseBase)
async def upload_note(
    file: UploadFile = File(...),
    auto_classify: bool = True,
    auto_keywords: bool = True,
    db: Session = Depends(get_db)
):
    file_content = await file.read()
    
    if not validate_image(file_content):
        raise HTTPException(status_code=400, detail="无效的图片格式，仅支持 JPG, PNG, BMP, GIF, WEBP")
    
    file_path = await save_upload_file(file_content, file.filename)
    relative_path = get_relative_path(file_path)
    
    ocr_service = OCRService()
    ocr_result = ocr_service.process_image(str(file_path))
    
    note_dao = NoteDAO(db)
    title = f"{datetime.now().strftime('%Y-%m-%d')} 笔记"
    
    content = ocr_result.text
    if AI_REFINE_OCR and ocr_result.text:
        ai_service = AIService()
        content = await ai_service.refine_ocr_content(ocr_result.text)
    
    category_id = None
    if auto_classify and content:
        classify_service = ClassifyService(db)
        category = classify_service.classify(content)
        if category:
            category_id = category.id
    
    keywords = []
    if auto_keywords and content:
        keyword_service = KeywordService()
        keywords = keyword_service.extract_keywords(content)
    
    note = note_dao.create(
        image_path=relative_path,
        title=title,
        content=content,
        category_id=category_id,
        keywords=keywords,
        ocr_confidence=ocr_result.confidence,
        source="upload"
    )
    
    category_dao = CategoryDAO(db)
    category = category_dao.get_by_id(category_id) if category_id else None
    
    markdown_service = MarkdownService()
    markdown_path = await markdown_service.save_markdown(note, category)
    note_dao.update(note.id, markdown_path=markdown_path, status="published")
    
    return ResponseBase(
        code=200,
        message="上传成功",
        data={
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "image_path": note.image_path,
            "category": {"id": category.id, "name": category.name} if category else None,
            "keywords": note.get_keywords_list(),
            "ocr_confidence": note.ocr_confidence,
            "created_at": note.created_at.isoformat()
        }
    )

@router.get("", response_model=ResponseBase)
def get_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    is_important: Optional[bool] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    note_dao = NoteDAO(db)
    skip = (page - 1) * page_size
    
    notes, total = note_dao.get_all(
        skip=skip,
        limit=page_size,
        category_id=category_id,
        is_important=is_important,
        keyword=keyword
    )
    
    items = []
    for note in notes:
        items.append({
            "id": note.id,
            "title": note.title,
            "content_preview": extract_preview(note.content),
            "image_path": note.image_path,
            "category": {"id": note.category.id, "name": note.category.name} if note.category else None,
            "keywords": note.get_keywords_list(),
            "is_important": note.is_important,
            "created_at": note.created_at.isoformat()
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

@router.get("/{note_id}", response_model=ResponseBase)
def get_note(note_id: int, db: Session = Depends(get_db)):
    note_dao = NoteDAO(db)
    note = note_dao.get_by_id(note_id)
    
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    return ResponseBase(
        code=200,
        message="success",
        data={
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "image_path": note.image_path,
            "markdown_path": note.markdown_path,
            "category": {"id": note.category.id, "name": note.category.name} if note.category else None,
            "keywords": note.get_keywords_list(),
            "is_important": note.is_important,
            "status": note.status,
            "ocr_confidence": note.ocr_confidence,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat()
        }
    )

@router.put("/{note_id}", response_model=ResponseBase)
def update_note(note_id: int, note_update: NoteUpdate, db: Session = Depends(get_db)):
    note_dao = NoteDAO(db)
    note = note_dao.get_by_id(note_id)
    
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    update_data = note_update.model_dump(exclude_unset=True)
    updated_note = note_dao.update(note_id, **update_data)
    
    return ResponseBase(
        code=200,
        message="更新成功",
        data={
            "id": updated_note.id,
            "title": updated_note.title,
            "updated_at": updated_note.updated_at.isoformat()
        }
    )

@router.delete("/{note_id}", response_model=ResponseBase)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note_dao = NoteDAO(db)
    note = note_dao.get_by_id(note_id)
    
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    note_dao.delete(note_id)
    
    return ResponseBase(code=200, message="删除成功")

@router.post("/{note_id}/reprocess", response_model=ResponseBase)
async def reprocess_note(note_id: int, db: Session = Depends(get_db)):
    note_dao = NoteDAO(db)
    note = note_dao.get_by_id(note_id)
    
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    ocr_service = OCRService()
    
    image_path = Path(note.image_path)
    if not image_path.is_absolute():
        image_path = IMAGES_DIR.parent / note.image_path
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="图片文件不存在")
    
    ocr_result = ocr_service.process_image(str(image_path))
    
    content = ocr_result.text
    if AI_REFINE_OCR and ocr_result.text:
        ai_service = AIService()
        content = await ai_service.refine_ocr_content(ocr_result.text)
    
    note_dao.update(
        note_id,
        content=content,
        ocr_confidence=ocr_result.confidence
    )
    
    return ResponseBase(
        code=200,
        message="重新处理完成",
        data={
            "id": note_id,
            "content": content,
            "ocr_confidence": ocr_result.confidence
        }
    )

@router.post("/{note_id}/classify", response_model=ResponseBase)
def classify_note(note_id: int, db: Session = Depends(get_db)):
    note_dao = NoteDAO(db)
    note = note_dao.get_by_id(note_id)
    
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    classify_service = ClassifyService(db)
    category = classify_service.classify(note.content)
    
    if category:
        note_dao.update(note_id, category_id=category.id)
    
    return ResponseBase(
        code=200,
        message="分类完成",
        data={
            "id": note_id,
            "category": {"id": category.id, "name": category.name} if category else None
        }
    )

@router.post("/{note_id}/keywords", response_model=ResponseBase)
def update_keywords(note_id: int, db: Session = Depends(get_db)):
    note_dao = NoteDAO(db)
    note = note_dao.get_by_id(note_id)
    
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    keyword_service = KeywordService()
    keywords = keyword_service.extract_keywords(note.content)
    
    note_dao.update(note_id, keywords=keywords)
    
    return ResponseBase(
        code=200,
        message="关键词提取完成",
        data={
            "id": note_id,
            "keywords": keywords
        }
    )

@router.post("/{note_id}/important", response_model=ResponseBase)
def toggle_important(note_id: int, db: Session = Depends(get_db)):
    note_dao = NoteDAO(db)
    note = note_dao.get_by_id(note_id)
    
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    new_status = not note.is_important
    note_dao.update(note_id, is_important=new_status)
    
    return ResponseBase(
        code=200,
        message="已更新",
        data={
            "id": note_id,
            "is_important": new_status
        }
    )


@router.get("/{note_id}/image")
def get_note_image(note_id: int, db: Session = Depends(get_db)):
    """获取笔记原图"""
    note_dao = NoteDAO(db)
    note = note_dao.get_by_id(note_id)
    
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    image_path = Path(note.image_path)
    if not image_path.is_absolute():
        image_path = IMAGES_DIR.parent / note.image_path
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="图片文件不存在")
    
    return FileResponse(str(image_path))
