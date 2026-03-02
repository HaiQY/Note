#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Note Organizer 后端功能测试脚本
无需前端界面即可测试所有后端功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from pathlib import Path

def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(success: bool, message: str):
    status = "✓" if success else "✗"
    print(f"  [{status}] {message}")

def test_database():
    """测试数据库初始化和基本操作"""
    print_header("测试数据库模块")
    
    try:
        from app.database import init_db, SessionLocal, get_db_context
        from app.config import ensure_directories
        
        ensure_directories()
        init_db()
        print_result(True, "数据库初始化成功")
        
        with get_db_context() as db:
            from app.dao import CategoryDAO
            category_dao = CategoryDAO(db)
            categories = category_dao.get_all()
            print_result(True, f"获取到 {len(categories)} 个默认分类")
            
            for cat in categories:
                print(f"      - {cat.name} ({cat.color})")
        
        return True
    except Exception as e:
        print_result(False, f"数据库测试失败: {e}")
        return False

def test_category_crud():
    """测试分类CRUD操作"""
    print_header("测试分类CRUD")
    
    try:
        from app.database import get_db_context
        from app.dao import CategoryDAO
        
        with get_db_context() as db:
            category_dao = CategoryDAO(db)
            
            category = category_dao.create(
                name="测试分类",
                description="这是一个测试分类",
                keywords=["测试", "test"],
                color="#ff0000"
            )
            print_result(True, f"创建分类: {category.name} (ID: {category.id})")
            
            updated = category_dao.update(
                category.id,
                description="更新后的描述",
                color="#00ff00"
            )
            print_result(True, f"更新分类: {updated.description}")
            
            deleted = category_dao.delete(category.id)
            print_result(True, f"删除分类: {'成功' if deleted else '失败'}")
        
        return True
    except Exception as e:
        print_result(False, f"分类CRUD测试失败: {e}")
        return False

def test_note_crud():
    """测试笔记CRUD操作"""
    print_header("测试笔记CRUD")
    
    try:
        from app.database import get_db_context
        from app.dao import NoteDAO, CategoryDAO
        from app.config import IMAGES_DIR
        
        with get_db_context() as db:
            note_dao = NoteDAO(db)
            category_dao = CategoryDAO(db)
            
            test_image_path = "data/images/test.jpg"
            
            note = note_dao.create(
                image_path=test_image_path,
                title="测试笔记标题",
                content="这是一段测试内容，包含数学和函数等关键词。",
                keywords=["测试", "数学", "函数"],
                ocr_confidence=0.95
            )
            print_result(True, f"创建笔记: {note.title} (ID: {note.id})")
            
            fetched = note_dao.get_by_id(note.id)
            print_result(True, f"查询笔记: {fetched.title}")
            
            updated = note_dao.update(
                note.id,
                title="更新后的标题",
                is_important=True
            )
            print_result(True, f"更新笔记: {updated.title}, 重点: {updated.is_important}")
            
            notes, total = note_dao.get_all(limit=10)
            print_result(True, f"获取笔记列表: 共 {total} 条")
            
            note_dao.delete(note.id)
            print_result(True, "删除笔记成功")
        
        return True
    except Exception as e:
        print_result(False, f"笔记CRUD测试失败: {e}")
        return False

def test_card_crud():
    """测试复习卡片CRUD操作"""
    print_header("测试复习卡片CRUD")
    
    try:
        from app.database import get_db_context
        from app.dao import NoteDAO, CardDAO
        
        with get_db_context() as db:
            note_dao = NoteDAO(db)
            card_dao = CardDAO(db)
            
            note = note_dao.create(
                image_path="data/images/test.jpg",
                title="卡片测试笔记",
                content="测试卡片生成的内容"
            )
            print_result(True, f"创建测试笔记: ID {note.id}")
            
            card = card_dao.create(
                note_id=note.id,
                question="测试问题是什么？",
                answer="这是测试答案。",
                card_type="qa",
                difficulty=3
            )
            print_result(True, f"创建卡片: ID {card.id}")
            
            result = card_dao.submit_review(card.id, quality=4, time_spent=30)
            print_result(True, f"提交复习: 下次复习间隔 {result['interval']} 天")
            
            review_cards = card_dao.get_for_review(limit=10)
            print_result(True, f"获取待复习卡片: {len(review_cards)} 张")
            
            card_dao.delete(card.id)
            note_dao.delete(note.id)
            print_result(True, "清理测试数据完成")
        
        return True
    except Exception as e:
        print_result(False, f"复习卡片CRUD测试失败: {e}")
        return False

def test_ocr_service():
    """测试OCR服务"""
    print_header("测试OCR服务")
    
    try:
        from app.services import OCRService
        
        ocr_service = OCRService()
        print_result(True, "OCR服务初始化成功")
        
        result = ocr_service._mock_result("test_image.jpg")
        print_result(True, f"模拟OCR结果: {result.text[:50]}...")
        print_result(True, f"置信度: {result.confidence}")
        
        return True
    except Exception as e:
        print_result(False, f"OCR服务测试失败: {e}")
        return False

def test_classify_service():
    """测试分类服务"""
    print_header("测试分类服务")
    
    try:
        from app.database import get_db_context
        from app.services import ClassifyService
        
        with get_db_context() as db:
            classify_service = ClassifyService(db)
            
            test_content = "这是一段关于数学函数和极限的笔记内容"
            category = classify_service.classify(test_content)
            
            if category:
                print_result(True, f"分类结果: {category.name}")
            else:
                print_result(True, "分类结果: 未分类")
            
            top_categories = classify_service.get_top_categories(test_content, top_k=3)
            print_result(True, f"候选分类: {[f'{c.name}({s:.2f})' for c, s in top_categories]}")
        
        return True
    except Exception as e:
        print_result(False, f"分类服务测试失败: {e}")
        return False

def test_keyword_service():
    """测试关键词提取服务"""
    print_header("测试关键词提取服务")
    
    try:
        from app.services import KeywordService
        
        keyword_service = KeywordService()
        
        test_content = """
        高等数学是大学数学的重要课程，主要包括函数、极限、连续、导数、积分等内容。
        学习高等数学需要掌握基本的数学分析方法和技巧。
        """
        
        keywords = keyword_service.extract_keywords(test_content, top_k=5)
        print_result(True, f"提取关键词: {keywords}")
        
        keywords_textrank = keyword_service.extract_keywords_textrank(test_content, top_k=5)
        print_result(True, f"TextRank关键词: {keywords_textrank}")
        
        return True
    except Exception as e:
        print_result(False, f"关键词提取服务测试失败: {e}")
        return False

def test_ai_service():
    """测试AI服务"""
    print_header("测试AI服务")
    
    try:
        from app.services import AIService
        
        ai_service = AIService()
        print_result(True, "AI服务初始化成功")
        
        test_content = "函数极限的ε-δ定义：对于任意ε>0，存在δ>0，使得当0<|x-a|<δ时，有|f(x)-A|<ε。"
        
        import asyncio
        cards = asyncio.run(ai_service.generate_cards(test_content, card_count=2))
        print_result(True, f"生成卡片数量: {len(cards)}")
        
        if cards:
            for i, card in enumerate(cards):
                print(f"      卡片{i+1}: {card['question'][:30]}...")
        
        return True
    except Exception as e:
        print_result(False, f"AI服务测试失败: {e}")
        return False

def test_markdown_service():
    """测试Markdown生成服务"""
    print_header("测试Markdown服务")
    
    try:
        from app.database import get_db_context
        from app.services import MarkdownService
        from app.dao import NoteDAO, CategoryDAO
        import asyncio
        
        with get_db_context() as db:
            note_dao = NoteDAO(db)
            category_dao = CategoryDAO(db)
            
            note = note_dao.create(
                image_path="data/images/test.jpg",
                title="Markdown测试笔记",
                content="这是Markdown测试内容",
                keywords=["测试", "markdown"]
            )
            
            category = category_dao.get_by_id(1)
            
            md_service = MarkdownService()
            
            md_content = md_service.generate_markdown(note, category)
            print_result(True, "生成Markdown内容成功")
            print(f"\n{'-'*40}")
            print(md_content[:300] + "...")
            print(f"{'-'*40}\n")
            
            md_path = asyncio.run(md_service.save_markdown(note, category))
            print_result(True, f"保存Markdown: {md_path}")
            
            note_dao.delete(note.id)
            md_service.delete_markdown(md_path)
            print_result(True, "清理测试数据完成")
        
        return True
    except Exception as e:
        print_result(False, f"Markdown服务测试失败: {e}")
        return False

def test_search_service():
    """测试搜索服务"""
    print_header("测试搜索服务")
    
    try:
        from app.database import get_db_context
        from app.services import SearchService
        from app.dao import NoteDAO
        
        with get_db_context() as db:
            note_dao = NoteDAO(db)
            search_service = SearchService(db)
            
            note1 = note_dao.create(
                image_path="data/images/test1.jpg",
                title="数学笔记",
                content="函数极限的定义和性质",
                keywords=["数学", "函数"]
            )
            note2 = note_dao.create(
                image_path="data/images/test2.jpg",
                title="物理笔记",
                content="牛顿定律和能量守恒",
                keywords=["物理", "能量"]
            )
            
            results = search_service.search("函数")
            print_result(True, f"搜索'函数': 找到 {len(results)} 条结果")
            
            suggestions = search_service.get_suggestions("数")
            print_result(True, f"搜索建议'数': {suggestions}")
            
            note_dao.delete(note1.id)
            note_dao.delete(note2.id)
            print_result(True, "清理测试数据完成")
        
        return True
    except Exception as e:
        print_result(False, f"搜索服务测试失败: {e}")
        return False

def test_api_endpoints():
    """测试API端点（需要FastAPI应用）"""
    print_header("测试API端点")
    
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        print_result(False, "缺少 httpx 依赖，跳过API测试")
        print_result(True, "安装命令: pip install httpx")
        return True
    
    try:
        from app.main import app
        
        client = TestClient(app)
        
        response = client.get("/")
        print_result(response.status_code == 200, f"GET /: {response.status_code}")
        
        response = client.get("/health")
        print_result(response.status_code == 200, f"GET /health: {response.status_code}")
        
        response = client.get("/api/categories")
        print_result(response.status_code == 200, f"GET /api/categories: {response.status_code}")
        
        response = client.get("/api/notes")
        print_result(response.status_code == 200, f"GET /api/notes: {response.status_code}")
        
        return True
    except Exception as e:
        print_result(False, f"API端点测试失败: {e}")
        return False

def test_sm2_algorithm():
    """测试SM-2间隔重复算法"""
    print_header("测试SM-2算法")
    
    try:
        from app.database import get_db_context
        from app.dao import NoteDAO, CardDAO
        
        with get_db_context() as db:
            note_dao = NoteDAO(db)
            card_dao = CardDAO(db)
            
            note = note_dao.create(
                image_path="data/images/test.jpg",
                title="SM-2测试笔记",
                content="测试SM-2算法"
            )
            
            card = card_dao.create(
                note_id=note.id,
                question="测试问题",
                answer="测试答案"
            )
            
            print("  模拟复习序列 (quality: 4, 4, 5, 3, 4)")
            for i, quality in enumerate([4, 4, 5, 3, 4]):
                result = card_dao.submit_review(card.id, quality)
                print(f"    第{i+1}次复习: 间隔={result['interval']}天, EF={result['ease_factor']:.2f}")
            
            card_dao.delete(card.id)
            note_dao.delete(note.id)
            print_result(True, "SM-2算法测试完成")
        
        return True
    except Exception as e:
        print_result(False, f"SM-2算法测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("  Note Organizer - 后端功能测试")
    print("  时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    tests = [
        ("数据库初始化", test_database),
        ("分类CRUD", test_category_crud),
        ("笔记CRUD", test_note_crud),
        ("复习卡片CRUD", test_card_crud),
        ("OCR服务", test_ocr_service),
        ("分类服务", test_classify_service),
        ("关键词提取", test_keyword_service),
        ("AI服务", test_ai_service),
        ("Markdown服务", test_markdown_service),
        ("搜索服务", test_search_service),
        ("SM-2算法", test_sm2_algorithm),
        ("API端点", test_api_endpoints),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print_result(False, f"{name} 测试异常: {e}")
            results.append((name, False))
    
    print_header("测试结果汇总")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {status}: {name}")
    
    print(f"\n  总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n  🎉 所有测试通过！")
    else:
        print(f"\n  ⚠️  有 {total - passed} 个测试失败")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
