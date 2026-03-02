import os
from pathlib import Path
from datetime import datetime
import uuid
import aiofiles
from app.config import IMAGES_DIR

def generate_image_path(filename: str, extension: str = None) -> Path:
    now = datetime.now()
    year_month = now.strftime("%Y/%m")
    dir_path = IMAGES_DIR / year_month
    dir_path.mkdir(parents=True, exist_ok=True)
    
    if extension is None:
        extension = Path(filename).suffix or ".jpg"
    elif not extension.startswith("."):
        extension = f".{extension}"
    
    unique_name = f"{uuid.uuid4().hex}{extension}"
    return dir_path / unique_name

async def save_upload_file(file_content: bytes, filename: str) -> Path:
    file_path = generate_image_path(filename)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_content)
    return file_path

def get_relative_path(full_path: Path) -> str:
    try:
        return str(full_path.relative_to(IMAGES_DIR.parent))
    except ValueError:
        return str(full_path)

def delete_file(file_path: str) -> bool:
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = IMAGES_DIR.parent / file_path
        if path.exists():
            path.unlink()
            return True
    except Exception:
        pass
    return False
