#!/usr/bin/env python3
"""
测试笔记图片API端点
"""
import sys
sys.path.insert(0, 'Y:\\Playground\\Note\\main')

try:
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # 测试API路由
    print("测试API路由...")
    print("=" * 50)

    # 1. 获取笔记列表
    print("\n1. 获取笔记列表...")
    response = client.get("/api/notes?page=1&page_size=5")
    if response.status_code == 200:
        data = response.json()
        if data.get('data', {}).get('items'):
            notes = data['data']['items']
            print(f"✓ 找到 {len(notes)} 条笔记")

            if notes:
                note_id = notes[0]['id']
                print(f"\n2. 测试图片API (笔记ID: {note_id})...")

                # 2. 测试图片API
                response = client.get(f"/api/notes/{note_id}/image")
                if response.status_code == 200:
                    print(f"✓ 图片API正常 (Status: {response.status_code})")
                    print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
                    print(f"  Content-Length: {len(response.content)} bytes")
                elif response.status_code == 404:
                    print(f"✗ 图片不存在 (Status: {response.status_code})")
                    print(f"  响应: {response.json()}")
                else:
                    print(f"✗ 图片API错误 (Status: {response.status_code})")
                    print(f"  响应: {response.text}")
        else:
            print("✗ 没有找到笔记")
    else:
        print(f"✗ 获取笔记列表失败 (Status: {response.status_code})")

    print("\n" + "=" * 50)
    print("测试完成!")

except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确的conda环境中运行")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
