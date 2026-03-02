from pathlib import Path
from datetime import datetime
from typing import Optional
import aiofiles
from app.config import MARKDOWN_DIR
from app.models.note import Note
from app.models.category import Category

class MarkdownService:
    def __init__(self):
        MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
    
    def generate_markdown(self, note: Note, category: Optional[Category] = None) -> str:
        title = note.title or f"笔记 {note.id}"
        date = note.created_at.strftime("%Y-%m-%d %H:%M") if note.created_at else ""
        category_name = category.name if category else "未分类"
        keywords = note.get_keywords_list()
        
        frontmatter = "---\n"
        frontmatter += f"title: {title}\n"
        frontmatter += f"date: {date}\n"
        frontmatter += f"category: {category_name}\n"
        frontmatter += f"keywords: {keywords}\n"
        frontmatter += "---\n\n"
        
        header = f"# {title}\n\n"
        
        image_section = ""
        if note.image_path:
            image_rel_path = self._get_relative_image_path(note.image_path)
            image_section = f"![笔记图片](../{image_rel_path})\n\n"
        
        content_section = "## 内容\n\n"
        if note.content:
            content_section += f"{note.content}\n\n"
        else:
            content_section += "*待添加内容*\n\n"
        
        keywords_section = "## 关键词\n\n"
        if keywords:
            keywords_section += " ".join([f"#{kw}" for kw in keywords]) + "\n"
        else:
            keywords_section += "*无关键词*\n"
        
        metadata_section = "\n---\n\n"
        metadata_section += f"- 创建时间：{date}\n"
        metadata_section += f"- 状态：{note.status}\n"
        if note.ocr_confidence:
            metadata_section += f"- OCR置信度：{note.ocr_confidence:.2%}\n"
        
        return frontmatter + header + image_section + content_section + keywords_section + metadata_section
    
    async def save_markdown(self, note: Note, category: Optional[Category] = None) -> str:
        category_name = category.name if category else "未分类"
        category_dir = MARKDOWN_DIR / category_name
        category_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{note.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path = category_dir / filename
        
        content = self.generate_markdown(note, category)
        
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(content)
        
        return str(file_path)
    
    async def save_markdown_content(self, note: Note, category: Optional[Category] = None, markdown_content: str = "") -> str:
        category_name = category.name if category else "未分类"
        category_dir = MARKDOWN_DIR / category_name
        category_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{note.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path = category_dir / filename
        
        title = note.title or f"笔记 {note.id}"
        date = note.created_at.strftime("%Y-%m-%d %H:%M") if note.created_at else ""
        keywords = note.get_keywords_list()
        
        frontmatter = "---\n"
        frontmatter += f"title: {title}\n"
        frontmatter += f"date: {date}\n"
        frontmatter += f"category: {category_name}\n"
        frontmatter += f"keywords: {keywords}\n"
        frontmatter += "---\n\n"
        
        if note.image_path:
            image_rel_path = self._get_relative_image_path(note.image_path)
            image_section = f"![笔记图片](../{image_rel_path})\n\n"
            markdown_content = image_section + markdown_content
        
        full_content = frontmatter + markdown_content
        
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(full_content)
        
        return str(file_path)
    
    def _get_relative_image_path(self, image_path: str) -> str:
        try:
            path = Path(image_path)
            if path.is_absolute():
                return str(path.name)
            return image_path
        except Exception:
            return image_path
    
    async def update_markdown(self, note: Note, category: Optional[Category] = None) -> Optional[str]:
        if note.markdown_path:
            old_path = Path(note.markdown_path)
            if old_path.exists():
                old_path.unlink()
        
        return await self.save_markdown(note, category)
    
    def delete_markdown(self, markdown_path: str) -> bool:
        if not markdown_path:
            return False
        
        try:
            path = Path(markdown_path)
            if path.exists():
                path.unlink()
                return True
        except Exception:
            pass
        
        return False
