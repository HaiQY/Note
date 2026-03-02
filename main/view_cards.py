#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
复习卡片查看工具
查看数据库中已有的卡片列表和详情
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

def list_cards():
    """列出所有卡片"""
    from app.database import get_db_context
    from app.dao import CardDAO, NoteDAO
    
    with get_db_context() as db:
        card_dao = CardDAO(db)
        note_dao = NoteDAO(db)
        
        cards, total = card_dao.get_all(limit=100)
        
        if not cards:
            print("\n  暂无卡片")
            return
        
        print(f"\n  共 {total} 张卡片\n")
        print("-" * 60)
        
        for card in cards:
            note = note_dao.get_by_id(card.note_id) if card.note_id else None
            note_title = note.title if note else "未知笔记"
            
            status = "待复习" if card.is_active else "已停用"
            if card.next_review:
                if card.next_review <= datetime.now():
                    status = "需复习"
                else:
                    days = (card.next_review - datetime.now()).days
                    status = f"{days}天后复习"
            
            print(f"\n  ID: {card.id} | {status} | 难度: {card.difficulty}/5")
            print(f"  类型: {card.card_type} | 笔记: {note_title[:30]}...")
            print(f"  问题: {card.question[:80]}...")
            print(f"  复习: {card.review_count}次 | 正确: {card.correct_count}次 | 因子: {card.ease_factor:.2f}")
        
        print("\n" + "-" * 60)

def show_card(card_id: int):
    """显示指定卡片详情"""
    from app.database import get_db_context
    from app.dao import CardDAO, NoteDAO
    
    with get_db_context() as db:
        card_dao = CardDAO(db)
        note_dao = NoteDAO(db)
        
        card = card_dao.get_by_id(card_id)
        
        if not card:
            print(f"\n  卡片 {card_id} 不存在")
            return
        
        note = note_dao.get_by_id(card.note_id) if card.note_id else None
        
        print("\n" + "=" * 60)
        print(f"  卡片详情 (ID: {card.id})")
        print("=" * 60)
        
        print(f"\n  类型: {card.card_type}")
        print(f"  难度: {card.difficulty}/5")
        print(f"  状态: {'启用' if card.is_active else '停用'}")
        
        if note:
            print(f"\n  所属笔记: {note.title}")
            print(f"  笔记分类: {note.category.name if note.category else '未分类'}")
        
        print("\n" + "-" * 60)
        print("  问题:")
        print("-" * 60)
        print(f"  {card.question}")
        
        print("\n" + "-" * 60)
        print("  答案:")
        print("-" * 60)
        print(f"  {card.answer}")
        
        print("\n" + "-" * 60)
        print("  学习记录:")
        print("-" * 60)
        print(f"  复习次数: {card.review_count}")
        print(f"  正确次数: {card.correct_count}")
        print(f"  难度因子: {card.ease_factor:.2f}")
        
        if card.next_review:
            print(f"  下次复习: {card.next_review.strftime('%Y-%m-%d %H:%M')}")
        if card.last_review:
            print(f"  上次复习: {card.last_review.strftime('%Y-%m-%d %H:%M')}")
        
        print("\n" + "=" * 60)

def review_cards():
    """获取待复习的卡片"""
    from app.database import get_db_context
    from app.dao import CardDAO
    
    with get_db_context() as db:
        card_dao = CardDAO(db)
        cards = card_dao.get_for_review(limit=20)
        
        if not cards:
            print("\n  当前没有需要复习的卡片")
            return
        
        print(f"\n  待复习卡片: {len(cards)} 张\n")
        
        for i, card in enumerate(cards, 1):
            print(f"  {i}. [ID:{card.id}] {card.question[:50]}...")
        
        print()

def main():
    print("\n" + "=" * 60)
    print("  复习卡片查看工具")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "list":
            list_cards()
        elif cmd == "review":
            review_cards()
        elif cmd.isdigit():
            show_card(int(cmd))
        else:
            print(f"\n  未知命令: {cmd}")
            print("  可用命令: list, review, <卡片ID>")
    else:
        print("""
  使用方法:
    python view_cards.py list      # 列出所有卡片
    python view_cards.py review    # 查看待复习卡片
    python view_cards.py <ID>     # 查看指定卡片详情
    
  示例:
    python view_cards.py list
    python view_cards.py 1
        """)
        
        choice = input("\n  输入命令 (list/review/ID): ").strip()
        
        if choice == "list":
            list_cards()
        elif choice == "review":
            review_cards()
        elif choice.isdigit():
            show_card(int(choice))

if __name__ == "__main__":
    main()
