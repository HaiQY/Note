#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Note Organizer - 完整功能测试脚本
指定图片路径，测试完整的笔记处理流程
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

def print_step(step: int, title: str):
    print(f"\n{'='*60}")
    print(f"  步骤 {step}: {title}")
    print('='*60)

def print_success(msg: str):
    print(f"  ✓ {msg}")

def print_info(msg: str):
    print(f"  → {msg}")

def print_data(label: str, data):
    print(f"\n  【{label}】")
    if isinstance(data, str):
        lines = data.split('\n')
        for line in lines[:20]:
            print(f"    {line}")
        if len(lines) > 20:
            print(f"    ... (共{len(lines)}行)")
    elif isinstance(data, list):
        for item in data[:10]:
            print(f"    • {item}")
        if len(data) > 10:
            print(f"    ... (共{len(data)}项)")
    else:
        print(f"    {data}")

class NoteProcessor:
    """笔记处理器 - 完整流程测试"""
    
    def __init__(self):
        from app.database import init_db, SessionLocal
        from app.config import ensure_directories
        
        ensure_directories()
        init_db()
        
        self.SessionLocal = SessionLocal
        self.db = SessionLocal()
        
        from app.dao import NoteDAO, CategoryDAO, CardDAO
        from app.services import OCRService, ClassifyService, KeywordService, AIService, MarkdownService
        
        self.note_dao = NoteDAO(self.db)
        self.category_dao = CategoryDAO(self.db)
        self.card_dao = CardDAO(self.db)
        self.ocr_service = OCRService()
        self.classify_service = ClassifyService(self.db)
        self.keyword_service = KeywordService()
        self.ai_service = AIService()
        self.markdown_service = MarkdownService()
        
        self.current_note = None
        self.current_category = None
    
    def process_image(self, image_path: str, auto_classify: bool = True, auto_keywords: bool = True):
        """处理图片的完整流程"""
        
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")
        
        print_step(1, "图片验证")
        print_info(f"图片路径: {image_path.absolute()}")
        print_info(f"文件大小: {image_path.stat().st_size / 1024:.1f} KB")
        print_success("图片文件验证通过")
        
        print_step(2, "OCR识别")
        print_info("正在进行OCR识别...")
        
        ocr_result = self.ocr_service.process_image(str(image_path))
        
        print_success(f"OCR识别完成，置信度: {ocr_result.confidence:.2%}")
        print_data("识别内容", ocr_result.text)
        
        from app.config import AI_REFINE_OCR
        refined_content = ocr_result.text
        
        if AI_REFINE_OCR and ocr_result.text:
            print_step(3, "AI整理OCR内容")
            print_info("正在使用AI整理OCR识别结果...")
            
            refined_content = asyncio.run(self.ai_service.refine_ocr_content(ocr_result.text))
            print_success("AI整理完成")
            print_data("整理后内容", refined_content)
        
        step_num = 4 if AI_REFINE_OCR else 3
        print_step(step_num, "智能分类")
        
        content_for_classify = refined_content if AI_REFINE_OCR else ocr_result.text
        
        if auto_classify and content_for_classify:
            self.current_category = self.classify_service.classify(content_for_classify)
            
            if self.current_category:
                print_success(f"自动分类: {self.current_category.name}")
                print_info(f"分类颜色: {self.current_category.color}")
                
                top_categories = self.classify_service.get_top_categories(content_for_classify, top_k=3)
                print_data("候选分类", [f"{c.name} (相似度: {s:.0%})" for c, s in top_categories])
            else:
                print_info("未能自动分类，将使用默认分类")
        else:
            print_info("跳过自动分类")
        
        step_num = 5 if AI_REFINE_OCR else 4
        print_step(step_num, "关键词提取")
        
        keywords = []
        content_for_keywords = refined_content if AI_REFINE_OCR else ocr_result.text
        
        if auto_keywords and content_for_keywords:
            keywords = self.keyword_service.extract_keywords(content_for_keywords, top_k=8)
            print_success(f"提取到 {len(keywords)} 个关键词")
            print_data("关键词列表", keywords)
            
            tfidf = self.keyword_service.calculate_tfidf(content_for_keywords)
            print_data("TF-IDF权重", [f"{k}: {v:.4f}" for k, v in list(tfidf.items())[:5]])
        
        step_num = 6 if AI_REFINE_OCR else 5
        print_step(step_num, "创建笔记记录")
        
        from app.utils import save_upload_file, get_relative_path
        
        with open(image_path, 'rb') as f:
            file_content = f.read()
        
        saved_path = asyncio.run(save_upload_file(file_content, image_path.name))
        relative_path = get_relative_path(saved_path)
        
        title = f"{datetime.now().strftime('%Y-%m-%d %H:%M')} 笔记"
        
        content_to_save = refined_content if AI_REFINE_OCR else ocr_result.text
        
        self.current_note = self.note_dao.create(
            image_path=relative_path,
            title=title,
            content=content_to_save,
            category_id=self.current_category.id if self.current_category else None,
            keywords=keywords,
            ocr_confidence=ocr_result.confidence,
            source="upload"
        )
        
        print_success(f"笔记创建成功，ID: {self.current_note.id}")
        print_info(f"标题: {self.current_note.title}")
        print_info(f"状态: {self.current_note.status}")
        
        return self.current_note
    
    def generate_markdown(self):
        """生成Markdown文件"""
        
        if not self.current_note:
            print_info("请先处理图片")
            return None
        
        from app.config import AI_REFINE_OCR
        step_num = 7 if AI_REFINE_OCR else 6
        print_step(step_num, "生成Markdown")
        
        md_content = self.markdown_service.generate_markdown(self.current_note, self.current_category)
        print_success("Markdown内容生成完成")
        print_data("Markdown预览", md_content[:500] + "...")
        
        md_path = asyncio.run(self.markdown_service.save_markdown(self.current_note, self.current_category))
        
        self.note_dao.update(self.current_note.id, markdown_path=str(md_path), status="published")
        
        print_success(f"Markdown文件已保存: {md_path}")
        
        return md_path
    
    def generate_cards(self, count: int = 5):
        """生成复习卡片"""
        
        if not self.current_note:
            print_info("请先处理图片")
            return []
        
        from app.config import AI_REFINE_OCR
        step_num = 8 if AI_REFINE_OCR else 7
        print_step(step_num, "AI生成复习卡片")
        
        print_info(f"正在生成 {count} 张复习卡片...")
        
        cards_data = asyncio.run(self.ai_service.generate_cards(
            content=self.current_note.content,
            card_count=count,
            card_types=["qa", "fill_blank"]
        ))
        
        created_cards = []
        for card_data in cards_data:
            card = self.card_dao.create(
                note_id=self.current_note.id,
                question=card_data["question"],
                answer=card_data["answer"],
                card_type=card_data.get("card_type", "qa"),
                difficulty=card_data.get("difficulty", 3)
            )
            created_cards.append(card)
        
        print_success(f"成功生成 {len(created_cards)} 张复习卡片")
        
        for i, card in enumerate(created_cards, 1):
            print(f"\n  卡片 {i} [{card.card_type}] 难度:{card.difficulty}")
            print(f"    问: {card.question}")
            print(f"    答: {card.answer[:100]}{'...' if len(card.answer) > 100 else ''}")
        
        return created_cards
    
    def simulate_review(self):
        """模拟复习流程"""
        
        if not self.current_note:
            print_info("请先处理图片")
            return
        
        from app.config import AI_REFINE_OCR
        step_num = 9 if AI_REFINE_OCR else 8
        print_step(step_num, "模拟复习流程")
        
        cards = self.card_dao.get_by_note(self.current_note.id)
        
        if not cards:
            print_info("没有可复习的卡片")
            return
        
        print_success(f"获取到 {len(cards)} 张待复习卡片")
        
        import random
        qualities = [3, 4, 5, 4, 3]
        
        for i, card in enumerate(cards[:3]):
            quality = qualities[i % len(qualities)]
            result = self.card_dao.submit_review(card.id, quality=quality, time_spent=random.randint(20, 60))
            
            print(f"\n  复习卡片 {i+1}: {card.question[:30]}...")
            print(f"    评分: {quality}/5")
            print(f"    下次复习: {result['interval']} 天后")
            print(f"    难度因子: {result['ease_factor']:.2f}")
            print(f"    复习次数: {result['review_count']}")
    
    def get_summary(self):
        """获取处理摘要"""
        
        from app.config import AI_REFINE_OCR
        step_num = 10 if AI_REFINE_OCR else 9
        print_step(step_num, "处理完成摘要")
        
        if not self.current_note:
            print_info("没有处理中的笔记")
            return
        
        note = self.note_dao.get_by_id(self.current_note.id)
        cards = self.card_dao.get_by_note(self.current_note.id)
        
        print(f"""
  笔记ID: {note.id}
  标题: {note.title}
  分类: {note.category.name if note.category else '未分类'}
  状态: {note.status}
  
  内容长度: {len(note.content) if note.content else 0} 字符
  关键词: {', '.join(note.get_keywords_list()) if note.get_keywords_list() else '无'}
  重点标记: {'是' if note.is_important else '否'}
  
  OCR置信度: {note.ocr_confidence:.2%}
  图片路径: {note.image_path}
  Markdown: {note.markdown_path or '未生成'}
  
  复习卡片: {len(cards)} 张
  
  创建时间: {note.created_at}
  更新时间: {note.updated_at}
        """)
    
    def close(self):
        """关闭数据库连接"""
        self.db.close()


def main():
    """主函数"""
    
    print("\n" + "="*60)
    print("  Note Organizer - 笔记处理测试")
    print("  时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    image_path = None
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        print("\n  使用方法:")
        print("    python test_note_flow.py <图片路径>")
        print("\n  示例:")
        print("    python test_note_flow.py test_image.jpg")
        print("    python test_note_flow.py ../data/images/test.png")
        print()
        
        image_path = input("  请输入图片路径（或按回车使用模拟数据）: ").strip()
        
        if not image_path:
            print("\n  将使用模拟数据进行测试...")
            
            processor = NoteProcessor()
            
            processor.current_note = processor.note_dao.create(
                image_path="data/images/mock.jpg",
                title="模拟测试笔记",
                content="""
高等数学笔记

一、函数极限的定义

设函数 f(x) 在点 x₀ 的某去心邻域内有定义。如果存在常数 A，对于任意给定的正数 ε，
总存在正数 δ，使得当 0 < |x - x₀| < δ 时，有 |f(x) - A| < ε，
则称 A 是函数 f(x) 当 x→x₀ 时的极限。

二、极限的性质

1. 唯一性：如果极限存在，则极限值唯一
2. 有界性：如果极限存在，则函数在该邻域内有界
3. 保号性：如果极限大于零，则存在邻域使函数值大于零

三、极限的运算法则

设 lim f(x) = A, lim g(x) = B，则：
- lim [f(x) ± g(x)] = A ± B
- lim [f(x) · g(x)] = A · B
- lim [f(x) / g(x)] = A / B (B ≠ 0)

四、重要极限

1. lim (sin x / x) = 1 (x→0)
2. lim (1 + 1/x)^x = e (x→∞)
                """,
                keywords=["极限", "函数", "数学", "定义", "性质"],
                ocr_confidence=0.95
            )
            
            processor.current_category = processor.classify_service.classify(processor.current_note.content)
            
            processor.generate_markdown()
            processor.generate_cards(3)
            processor.simulate_review()
            processor.get_summary()
            
            processor.close()
            return
    
    try:
        processor = NoteProcessor()
        
        processor.process_image(image_path, auto_classify=True, auto_keywords=True)
        processor.generate_markdown()
        processor.generate_cards(5)
        processor.simulate_review()
        processor.get_summary()
        
        processor.close()
        
        print("\n" + "="*60)
        print("  ✓ 测试完成！")
        print("="*60 + "\n")
        
    except FileNotFoundError as e:
        print(f"\n  ✗ 错误: {e}\n")
    except Exception as e:
        print(f"\n  ✗ 处理失败: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
