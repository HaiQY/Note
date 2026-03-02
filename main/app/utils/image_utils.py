from PIL import Image
import io
from pathlib import Path
from typing import Tuple

SUPPORTED_FORMATS = {"jpg", "jpeg", "png", "bmp", "gif", "webp"}

def validate_image(file_content: bytes) -> bool:
    try:
        img = Image.open(io.BytesIO(file_content))
        img.verify()
        return True
    except Exception:
        return False

def get_image_info(file_content: bytes) -> dict:
    try:
        img = Image.open(io.BytesIO(file_content))
        return {
            "format": img.format,
            "size": img.size,
            "mode": img.mode,
            "width": img.width,
            "height": img.height
        }
    except Exception:
        return {}

def resize_image(file_content: bytes, max_size: Tuple[int, int] = (1920, 1920)) -> bytes:
    img = Image.open(io.BytesIO(file_content))
    
    if img.width > max_size[0] or img.height > max_size[1]:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    output = io.BytesIO()
    img_format = img.format or "JPEG"
    if img_format == "JPEG":
        img = img.convert("RGB")
    img.save(output, format=img_format, quality=85)
    return output.getvalue()

def convert_to_jpg(file_content: bytes) -> bytes:
    img = Image.open(io.BytesIO(file_content))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85)
    return output.getvalue()

def get_image_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower().lstrip(".")
    return ext if ext in SUPPORTED_FORMATS else "jpg"
