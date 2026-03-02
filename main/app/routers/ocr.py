from fastapi import APIRouter, UploadFile, File
from app.schemas import ResponseBase
from app.services import OCRService

router = APIRouter(prefix="/api/ocr", tags=["ocr"])

@router.post("/process", response_model=ResponseBase)
async def process_image(file: UploadFile = File(...)):
    file_content = await file.read()
    
    ocr_service = OCRService()
    result = ocr_service.process_image_bytes(file_content)
    
    return ResponseBase(
        code=200,
        message="处理完成",
        data={
            "text": result.text,
            "confidence": result.confidence
        }
    )
