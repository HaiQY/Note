import json
import re
from typing import List

from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, ZHIPU_API_KEY
from app.logger import logger


class AIService:
    def __init__(self):
        self.client = None
        self.zhipu_client = None
        
        if OPENAI_API_KEY:
            try:
                from openai import OpenAI
                client_kwargs = {"api_key": OPENAI_API_KEY}
                if OPENAI_BASE_URL:
                    client_kwargs["base_url"] = OPENAI_BASE_URL
                self.client = OpenAI(**client_kwargs)
            except ImportError:
                pass
        
        if ZHIPU_API_KEY:
            try:
                from zai import ZhipuAiClient
                self.zhipu_client = ZhipuAiClient(api_key=ZHIPU_API_KEY)
            except ImportError:
                pass
    
    async def generate_cards(
        self,
        content: str,
        card_count: int = 5,
        card_types: List[str] = None
    ) -> List[dict]:
        if card_types is None:
            card_types = ["qa"]
        
        prompt = self._build_prompt(content, card_count, card_types)
        
        if self.client:
            return await self._generate_with_api(prompt, card_count)
        
        return self._generate_mock_cards(content, card_count, card_types)
    
    def _build_prompt(self, content: str, card_count: int, card_types: List[str]) -> str:
        return f"""
请根据以下笔记内容生成{card_count}张复习卡片。

笔记内容：
{content}

要求：
1. 问题应覆盖核心概念和重要知识点
2. 答案应简洁准确
3. 难度适中
4. 卡片类型包括: {', '.join(card_types)}

输出JSON格式：
{{
    "cards": [
        {{
            "question": "问题内容",
            "answer": "答案内容",
            "card_type": "qa|fill_blank",
            "difficulty": 1-5
        }}
    ]
}}
"""
    
    async def _generate_with_api(self, prompt: str, card_count: int) -> List[dict]:
        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个专业的学习助手，擅长根据笔记内容生成高质量的复习卡片。"},
                    {"role": "user", "content": prompt}
                ],
                extra_body={
                    "thinking": {"type": "disabled"}
                },
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {e}")
                    return []
            else:
                logger.warning("No JSON found in response")
                return []
            
            return data.get("cards", [])
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return []
    
    def _generate_mock_cards(self, content: str, card_count: int, card_types: List[str]) -> List[dict]:
        cards = []
        content_preview = content[:200] if content else "测试内容"
        
        for i in range(min(card_count, 3)):
            cards.append({
                "question": f"关于笔记内容的问题 {i+1}？（模拟生成）",
                "answer": f"这是答案 {i+1}。内容摘要：{content_preview[:50]}...",
                "card_type": card_types[0] if card_types else "qa",
                "difficulty": 3
            })
        
        return cards
    
    async def summarize(self, content: str) -> str:
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "你是一个专业的学习助手，请简洁地总结笔记内容。"},
                        {"role": "user", "content": f"请总结以下内容：\n\n{content}"}
                    ],
                    max_tokens=500
                )
                return response.choices[0].message.content or ""
            except Exception:
                pass
        
        return f"[摘要] {content[:100]}..." if content else ""
    
    async def refine_ocr_content(self, content: str) -> str:
        if self.zhipu_client:
            try:
                response = self.zhipu_client.chat.completions.create(
                    model="glm-4.7-flash",
                    messages=[
                        {
                            "role": "system", 
                            "content": """你是一个专业的笔记整理助手。
你的任务是对OCR识别的笔记内容进行整理和修正。

常见OCR错误类型：
- 错别字：如"们的心"应为"它们的中心"，"到立"应为"倒立"
- 漏字：如"缩"应为"缩小"
- 表格格式混乱
- 标点符号缺失或错误

整理要求：
1. 修正所有明显的OCR识别错误
2. 还原表格格式（使用Markdown表格语法），但其它地方不要使用Markdown语法
3. 补充正确的标点符号
4. 使内容结构清晰、易读
5. 直接输出整理后的内容，不要解释做了哪些修改"""
                        },
                        {"role": "user", "content": f"请整理以下OCR识别的物理笔记内容（这是一份关于凸透镜成像规律的笔记）：\n\n{content}"}
                    ],
                    thinking={"type": "disabled"},
                    max_tokens=128000,
                )
                result = response.choices[0].message.content or content
                return result
            except Exception as e:
                logger.error(f"ZhipuAI refine OCR failed: {e}")
        
        return content