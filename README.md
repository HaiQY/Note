# 手写笔记智能整理工具 - 完整文档

> Note Organizer - 基于AI的手写笔记智能整理系统

一套完整的手写笔记智能处理平台，从图片拍摄到知识管理，实现笔记的自动识别、分类、整理和复习。

## 📋 目录

- [项目概述](#项目概述)
- [核心功能](#核心功能)
- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [核心模块详解](#核心模块详解)
- [算法原理](#算法原理)
- [快速开始](#快速开始)
- [API文档](#api文档)
- [数据库模式](#数据库模式)

---

## 项目概述

**Note Organizer** 是一个端到端的笔记智能化处理系统，专门设计用于处理手写笔记图片。系统集成了多种AI技术，为用户提供：

- 📸 **高精度OCR识别** - 基于PaddleOCR的中文文本提取
- 🏷️ **自动分类** - 基于关键词的智能分类算法
- 🔍 **关键词提取** - TF-IDF和TextRank算法相结合
- 🤖 **AI驱动卡片生成** - 利用GPT生成复习卡片
- 📝 **Markdown文档生成** - 自动生成结构化文档
- 🔎 **全文搜索** - 支持多条件全文搜索
- 💾 **数据持久化** - SQLite数据库存储

### 技术指标

| 指标 | 说明 |
|------|------|
| **Python版本** | 3.12.12 |
| **主框架** | FastAPI 0.131.0 |
| **数据库** | SQLite (可扩展到PostgreSQL) |
| **部署方式** | 本地单机运行 |
| **OCR引擎** | PaddleOCR 3.4.0 |

---

## 核心功能

### 1️⃣ 笔记上传与OCR识别

**流程**：上传笔记图片 → 自动OCR识别 → 提取文本

**特性**：
- 支持多种图片格式 (JPG, PNG, BMP, GIF, WEBP)
- 自动倾斜矫正（使用角度分类器）
- 可选的AI优化（通过GPT对OCR结果进行校正）
- 返回置信度评分

**相关文件**：
- `app/services/ocr_service.py` - OCR核心服务
- `app/routers/notes.py` - 笔记上传API

### 2️⃣ 文档结构识别

**流程**：原始图片 → 结构分析 → 表格识别 → 公式识别 → Markdown生成

**特性**：
- 使用 PPStructureV3 进行文档元素识别
- 支持表格识别和转换为Markdown表格
- 支持公式识别（PP-FormulaNet）
- 图表识别和Mermaid图表生成
- GPU加速支持

**支持的元素**：
- 📊 表格 (HTML/Markdown格式)
- 📐 数学公式 (LaTeX格式)
- 📈 流程图/关系图 (Mermaid格式)
- 🖼️ 图像区域识别

**相关文件**：
- `app/services/structure_service.py` - 文档结构服务

### 3️⃣ 自动分类

**算法**：基于关键词匹配的相似度计算

**流程**：
1. 提取文本中的关键词
2. 遍历所有分类候选项
3. 计算文本与分类关键词的匹配度
4. 选择匹配度最高的分类（或默认"其他"）

**相似度计算公式**：
$$\text{similarity} = \frac{\text{匹配关键词数}}{\text{分类总关键词数}}$$

**相关文件**：
- `app/services/classify_service.py`

### 4️⃣ 关键词提取

**支持三种算法**：

| 算法 | 说明 | 适用场景 |
|------|------|--------|
| **连续 TF-IDF** | 基于词频-逆文本频率 | 通用、快速、效果好 |
| **TextRank** | 利用图算法计算重要性 | 长文本、学术文本 |
| **Jieba分词+过滤** | 保留名词和动词，去除停词 | 中文特化 |

**关键词提取步骤**：
1. 文本预处理 (清理标点、转小写)
2. 中文分词 (使用jieba)
3. 权重计算 (TF-IDF或TextRank)
4. 停词过滤 (去除常用词)
5. 取Top-K结果

**相关文件**：
- `app/services/keyword_service.py`

### 5️⃣ AI驱动卡片生成

**流程**：笔记内容 → GPT API → 生成Q&A卡片

**生成策略**：
- 支持多种卡片类型 (选择题、填空题、简答题等)
- 可配置卡片数量
- 自动计算难度等级（1-5）

**卡片算法 - SM-2间隔重复**：
- 用户评分(0-5) → 更新ease_factor
- 更新复习间隔 (exponential backoff)
- 计算下次复习时间

**公式**（SM-2算法）：
$$I(1) = 1, I(2) = 3$$
$$I(n) = I(n-1) \times E_F$$
$$E_F = E_F + (0.1 - (5-q) \times (0.08 + (5-q) \times 0.02))$$

其中 $q$ 是回答质量（0-5），$E_F$ 是易度因子。

**相关文件**：
- `app/services/ai_service.py`
- `app/routers/cards.py`

### 6️⃣ 全文搜索

**搜索功能**：
- 支持按标题、内容、关键词搜索
- 支持按分类、时间范围筛选
- 自动计算相关性评分
- 返回搜索结果高亮

**评分规则**：
$$\text{score} = I_{title} \times 2 + I_{content} + I_{keywords} \times 0.5$$

其中 $I_{*}$ 为各部分的匹配指示器。

**相关文件**：
- `app/services/search_service.py`

### 7️⃣ Markdown文档生成

**生成结构**：
```
---
title: 笔记标题
date: 2026-03-03 12:34
category: 物理
keywords: [光学, 光波, 干涉]
---

# 笔记标题

![笔记图片](../images/2026/03/xxx.jpg)

## 内容
[OCR识别的文本内容]

## 关键词
#光学 #光波 #干涉

---
- 创建时间：2026-03-03 12:34
- 状态：published
- OCR置信度：92.30%
```

**相关文件**：
- `app/services/markdown_service.py`

---

## 项目结构

```
Note/
├── __init__.py
├── README.md (原简要说明)
├── README_DETAILED.md (本文件 - 完整文档)
├── requirements.txt (依赖列表)
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI应用入口
│   ├── config.py                    # 环境配置管理
│   ├── database.py                  # 数据库初始化与连接
│   ├── models/                      # 数据模型(ORM)
│   │   ├── __init__.py
│   │   ├── base.py                  # 基础模型(时间戳mixin)
│   │   ├── note.py                  # Note - 笔记模型
│   │   ├── card.py                  # ReviewCard - 卡片模型
│   │   └── category.py              # Category - 分类模型
│   ├── schemas/                     # 数据验证方案(Pydantic)
│   │   ├── __init__.py
│   │   ├── common.py                # 通用响应方案
│   │   ├── note.py                  # 笔记相关方案
│   │   ├── card.py                  # 卡片相关方案
│   │   └── category.py              # 分类相关方案
│   ├── routers/                     # API路由
│   │   ├── __init__.py              # 路由聚合器
│   │   ├── notes.py                 # /api/notes/* 路由
│   │   ├── categories.py            # /api/categories/* 路由
│   │   ├── cards.py                 # /api/cards/* 路由
│   │   ├── search.py                # /api/search/* 路由
│   │   └── ocr.py                   # /api/ocr/* 路由
│   ├── services/                    # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── ocr_service.py           # OCR识别服务
│   │   ├── structure_service.py     # 文档结构识别服务
│   │   ├── classify_service.py      # 自动分类服务
│   │   ├── keyword_service.py       # 关键词提取服务
│   │   ├── ai_service.py            # AI卡片生成服务
│   │   ├── search_service.py        # 搜索服务
│   │   └── markdown_service.py      # Markdown生成服务
│   ├── dao/                         # 数据访问层
│   │   ├── __init__.py
│   │   ├── note_dao.py              # Note DAO
│   │   ├── card_dao.py              # ReviewCard DAO
│   │   └── category_dao.py          # Category DAO
│   ├── utils/                       # 工具函数
│   │   ├── __init__.py
│   │   ├── file_utils.py            # 文件操作
│   │   ├── image_utils.py           # 图片处理
│   │   └── text_utils.py            # 文本处理
│   └── static/                      # 前端静态文件(可选)
│       ├── index.html
│       ├── api.js
│       └── ...
├── data/                            # 数据存储
│   ├── images/                      # 笔记图片
│   │   └── 2026/03/*
│   ├── markdown/                    # 生成的Markdown文件
│   │   ├── 物理/
│   │   ├── 其他/
│   │   └── 未分类/
│   └── cards/                       # 卡片数据(可选)
└── docs/                            # 文档
    ├── 研究报告.md
    └── ...
```

---

## 技术栈

### 后端框架

| 组件 | 版本 | 用途 |
|------|------|------|
| **FastAPI** | 0.131.0 | Web框架 |
| **Uvicorn** | 0.41.0 | ASGI服务器 |
| **Pydantic** | 2.12.5 | 数据验证 |
| **SQLAlchemy** | 2.0.46 | ORM框架 |

### AI/ML 模块

| 组件 | 版本 | 用途 |
|------|------|------|
| **PaddleOCR** | 3.4.0 | 文本识别(Chinese) |
| **PaddlePaddle** | 3.3.0 | 深度学习框架(GPU) |
| **OpenAI SDK** | 2.21.0 | GPT API调用 |

### 自然语言处理

| 组件 | 版本 | 用途 |
|------|------|------|
| **Jieba** | 0.42.1 | 中文分词 |

### 计算机视觉

| 组件 | 版本 | 用途 |
|------|------|------|
| **Pillow** | 12.1.0 | 图像处理 |
| **OpenCV** | 4.10.0.84 | 视觉处理 |

### 其他

| 组件 | 版本 | 用途 |
|------|------|------|
| **python-dotenv** | 1.2.1 | 环境变量管理 |
| **aiofiles** | ≥23.0.0 | 异步文件操作 |
| **httpx** | ≥0.24.0 | 异步HTTP客户端 |

---

## 核心模块详解

### 模型层 (Models)

#### 📌 Note (笔记)
```python
class Note(TimestampMixin, Base):
    id: int                    # 主键
    title: str                 # 笔记标题
    content: str               # 原始OCR识别内容
    clean_content: str         # 清理后的内容
    image_path: str            # 笔记图片路径
    markdown_path: str         # 生成的Markdown文件路径
    category_id: int           # 所属分类(FK)
    keywords: str              # JSON格式的关键词列表
    is_important: bool         # 是否标记为重要
    status: str                # 状态("draft", "published", etc)
    ocr_confidence: float      # OCR置信度(0-1)
    source: str                # 数据来源("upload", "import", etc)
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
```

**关系**：
- `category`: 多对一关系 → Category
- `review_cards`: 一对多关系 → ReviewCard

#### 💳 ReviewCard (复习卡片)
```python
class ReviewCard(TimestampMixin, Base):
    id: int                    # 主键
    note_id: int               # 关联笔记(FK)
    question: str              # 问题内容
    answer: str                # 答案内容
    card_type: str             # 卡片类型("qa", "fill_blank", etc)
    difficulty: int            # 难度(1-5)
    next_review: datetime      # 下次复习时间
    interval: int              # 复习间隔(天)
    ease_factor: float         # SM-2易度因子(默认2.5)
    review_count: int          # 总复习次数
    correct_count: int         # 正确次数
    last_review: datetime      # 上次复习时间
    is_active: bool            # 是否激活
```

**复习算法**：采用SM-2间隔重复算法
- 根据用户回答质量调整重复间隔
- 自适应难度调整

#### 🏷️ Category (分类)
```python
class Category(TimestampMixin, Base):
    id: int                    # 主键
    name: str                  # 分类名称(唯一)
    description: str           # 分类描述
    keywords: str              # JSON格式的分类关键词
    color: str                 # 显示颜色(hex)
    icon: str                  # 图标名称
    sort_order: int            # 排序顺序
```

### 服务层 (Services)

#### 🔍 OCRService - 文本识别

**核心方法**：
- `process_image(image_path: str) -> OCRResult` - 识别单张图片
- `process_image_bytes(file_content: bytes) -> OCRResult` - 识别图片字节

**输出**：
```python
class OCRResult:
    text: str                  # 识别的文本
    confidence: float          # 置信度(0-1)
    boxes: List[List[int]]     # 文本框坐标(可选)
```

**实现细节**：
- 单例模式 (同一进程只初始化一次)
- 使用PaddleOCR进行识别
- 支持角度矫正 (use_angle_cls=True)
- 可降级处理 (PaddleOCR不可用时返回mock数据)

---

#### 📊 StructureService - 文档结构识别

**核心方法**：
- `process_image(image_path: str) -> StructureResult` - 完整的文档分析
- `extract_diagram_structure(image_path: str) -> Dict` - 图表结构提取
- `generate_mermaid(diagram_struct: Dict) -> str` - 生成Mermaid图表代码

**输出**：
```python
class StructureResult:
    text: str                  # 识别的文本
    markdown: str              # 生成的Markdown
    confidence: float          # 置信度
    formula_count: int         # 公式数量
    table_count: int           # 表格数量
    image_regions: List        # 图像区域
    formula_regions: List      # 公式区域
    table_regions: List        # 表格区域
    diagram_regions: List      # 图表区域
```

**识别元素**：
- 📝 纯文本区域 (通过OCR)
- 📊 表格 (自动转Markdown表格)
- 📐 数学公式 (PP-FormulaNet)
- 📈 图表/图形 (可转Mermaid)

---

#### 🤖 ClassifyService - 自动分类

**核心方法**：
- `classify(content: str) -> Category` - 自动分类
- `calculate_similarity(content: str, category: Category) -> float` - 计算相似度
- `get_top_categories(content: str, top_k: int = 3) -> List[tuple]` - 获取Top-K分类

**算法**：
1. 遍历所有分类
2. 统计分类关键词在内容中出现的次数
3. 计算匹配度 = 匹配次数 / 分类关键词总数
4. 选择最高匹配度的分类

**示例**：
```
分类"物理": 关键词 = ["光学", "波长", "干涉"]
内容: "光学实验中观察到干涉现象..."
匹配: ["光学", "干涉"] = 2个
相似度 = 2 / 3 = 66.7%
```

---

#### 🔑 KeywordService - 关键词提取

**核心方法**：
- `extract_keywords(content: str, top_k: int = 5) -> List[str]` - TF-IDF提取
- `extract_keywords_textrank(content: str, top_k: int = 5) -> List[str]` - TextRank提取
- `calculate_tfidf(content: str) -> Dict` - 计算TF-IDF权重

**流程**：
1. 文本清理 (去除标点、规范化)
2. 中文分词 (Jieba库)
3. 权重计算 (TF-IDF或TextRank)
4. 停词过滤 (移除常用词)
5. 排序和取Top-K

**停词表**：包含中文和英文常用词
- 中文：的、是、在、了、和、等
- 英文：the、a、is、was、have等

**算法对比**：
- **TF-IDF**：计算快，适合快速提取，全局视角
- **TextRank**：质量高，适合学术文本，基于图论

---

#### 🤖 AIService - AI驱动服务

**核心方法**：
- `generate_cards(content: str, card_count: int, card_types: List) -> List[dict]` - 生成卡片
- `refine_ocr_content(content: str) -> str` - 优化OCR结果

**集成API**：
- OpenAI GPT (可配置base_url)
- 智谱AI (备选方案)

**生成策略**：
```
输入：笔记内容 + 卡片数量 + 卡片类型
↓
构建Prompt (包含内容、要求、输出格式)
↓
调用GPT API
↓
解析JSON响应
↓
输出：List[{question, answer, card_type, difficulty}]
```

---

#### 🔎 SearchService - 全文搜索

**核心方法**：
- `search(query, category_id, date_from, date_to, limit) -> List[dict]` - 全文搜索
- `get_suggestions(partial: str, limit: int) -> List[str]` - 搜索建议
- `_highlight_text(text: str, query: str) -> str` - 生成高亮
- `_calculate_score(note: Note, query: str) -> float` - 计算相关性评分

**评分规则**：
```
总分 = 标题匹配×2 + 内容匹配×1 + 关键词匹配×0.5
```

**搜索条件**：
- 关键词（title/content/keywords）
- 分类ID
- 时间范围

---

#### 📝 MarkdownService - Markdown生成

**核心方法**：
- `generate_markdown(note, category) -> str` - 生成Markdown内容
- `save_markdown(note, category) -> str` - 保存为文件
- `save_markdown_content(note, category, markdown_content) -> str` - 保存预生成内容

**生成的结构**：
```markdown
---
title: 笔记标题
date: YYYY-MM-DD HH:MM
category: 分类名
keywords: [keyword1, keyword2, ...]
---

# 标题

![笔记图片](../images/path/to/image.jpg)

## 内容
[OCR识别的文本]

## 关键词
#keyword1 #keyword2

---
- 创建时间：...
- 状态：...
- OCR置信度：...%
```

**特性**：
- YAML Frontmatter 用于元数据
- 自动图片相对路径处理
- 支持两种生成模式（普通和Structure模式）

---

### 数据访问层 (DAO)

使用DAO模式封装数据库操作，提供统一的数据访问接口。

#### NoteDAO
```python
# 常用方法
create(data) -> Note              # 创建笔记
get_by_id(id) -> Note             # 获取笔记
update(id, **fields) -> Note      # 更新笔记
delete(id) -> bool                # 删除笔记
get_all(skip, limit) -> List      # 获取列表
search(query_text, ...) -> List   # 全文搜索
```

#### CategoryDAO
```python
get_by_name(name) -> Category     # 按名称获取
get_all() -> List[Category]       # 获取所有分类
init_default_categories()         # 初始化默认分类
```

#### CardDAO
```python
create(note_id, question, ...) -> Card  # 创建卡片
update_review(id, quality) -> Card      # 更新复习记录
get_due_cards() -> List                 # 获取待复习卡片
```

---

## 算法原理

### 1. 自动分类算法

**算法名称**：关键词匹配相似度

**步骤**：
```
输入：笔记内容, 分类列表
↓
foreach 分类:
    keywords = 分类.关键词列表
    match_count = 0
    for 关键词 in keywords:
        if 关键词 in 笔记内容:
            match_count += 1
    相似度 = match_count / len(keywords)
↓
最优分类 = argmax(相似度)
输出：相似度最高的分类
```

**复杂度**：O(n × m)，n=分类数，m=平均关键词数

---

### 2. 关键词提取算法

#### 2.1 TF-IDF 算法

**定义**：
$$\text{TF}(t,d) = \frac{f_{t,d}}{\sum_i f_{i,d}}$$

$$\text{IDF}(t) = \log\frac{N}{n_t}$$

$$\text{TF-IDF}(t,d) = \text{TF}(t,d) \times \text{IDF}(t)$$

其中：
- $f_{t,d}$ = 词t在文档d中的频次
- $N$ = 文档总数
- $n_t$ = 包含词t的文档数

**特点**：
- ✅ 简单快速
- ✅ 易于并行化
- ❌ 无法判断词的重要性
- ❌ 不考虑词的位置和上下文

#### 2.2 TextRank 算法

**基于图论的关键词提取**：

1. **构建图**：用词作为节点，词的共现作为边
2. **计算权重**：使用PageRank算法迭代计算
3. **排序提取**：按权重排序，取Top-K

**公式**：
$$\text{TextRank}(i) = (1-d) + d \cdot \sum_{j \in in(i)} \frac{1}{|out(j)|} \cdot \text{TextRank}(j)$$

**特点**：
- ✅ 考虑词的相关性
- ✅ 无需语料库支持
- ❌ 计算复杂度较高
- ❌ 对长文本效果更好

---

### 3. SM-2 间隔重复算法

**应用场景**：复习卡片的复习安排

**核心参数**：
- `interval` (I) - 复习间隔（天）
- `ease_factor` (E) - 难度因子（通常2.5）
- `quality` (q) - 用户回答质量（0-5）

**更新规则**：

**初始化**：
$$I(1) = 1 \text{ day}, I(2) = 3 \text{ days}, E = 2.5$$

**第n次复习后**：
$$I(n) = I(n-1) \times E$$

$$E' = E + (0.1 - (5-q) \times (0.08 + (5-q) \times 0.02))$$

**下次复习时间**：
$$\text{next\_review} = \text{today} + I(n) \text{ days}$$

**质量评分**：
- 0-2：完全遗忘（重置为初始）
- 3-4：模糊记忆（减小间隔）
- 5：完全掌握（增加间隔）

**示例**：

| 回答 | 质量q | 新E值 | 新间隔 |
|------|------|------|--------|
| 遗忘 | 1 | 1.96 | 1天 |
| 模糊 | 3 | 2.36 | 3天 |
| 完美 | 5 | 2.50 | I×2.5天 |

---

### 4. 搜索相关性评分算法

**公式**：
$$\text{score}(note, query) = I_{\text{title}} \times 2 + I_{\text{content}} + \sum_{kw \in keywords} I_{\text{keyword}(kw)} \times 0.5$$

其中 $I_{*}$ 为指示函数（匹配=1，不匹配=0）

**例子**：
```
查询："光学干涉"
笔记1：
  - 标题："光学干涉实验" → 标题匹配 ×2 = 2.0
  - 内容：包含"光学干涉" → 内容匹配 ×1 = 1.0
  - 关键词：["光学", "干涉", "波长"] → 2个关键词匹配 ×0.5 = 1.0
  - 总分 = 2.0 + 1.0 + 1.0 = 4.0

笔记2：
  - 标题："光的衍射" → 无匹配 = 0.0
  - 内容：包含"光学" → 内容匹配 ×1 = 1.0
  - 关键词：["光学"] → 1个关键词匹配 ×0.5 = 0.5
  - 总分 = 0.0 + 1.0 + 0.5 = 1.5

排序结果：笔记1 (4.0) > 笔记2 (1.5)
```

---

## 快速开始

### 前置要求

- Python 3.12+
- PaddleOCR 依赖 (PaddlePaddle GPU版本)
- OpenAI API Key (用于卡片生成)
- 8GB+ 内存 (推荐16GB用于GPU)

### 安装步骤

<br/>

**1. 克隆项目**
```bash
cd /path/to/project
```

**2. 创建虚拟环境** (可选但推荐)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

**3. 安装依赖**
```bash
pip install -r requirements.txt
```

**4. 配置环境变量**

创建 `.env` 文件：
```bash
# 应用配置
APP_NAME="Note Organizer"
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# 数据库
DATABASE_URL=sqlite:///./data/notes.db

# OCR配置
OCR_LANG=ch
USE_STRUCTURE_V3=true
STRUCTURE_DEVICE=gpu  # 或 cpu

# AI配置
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
AI_REFINE_OCR=true

# 可选：智谱AI
ZHIPU_API_KEY=your-zhipu-key

# 日志
LOG_LEVEL=INFO
```

**5. 初始化数据库**
```bash
python -c "from app.database import init_db; init_db()"
```

**6. 启动服务**
```bash
python app/main.py
```

访问：http://localhost:8000

---

## API文档

### 通用响应格式

所有API响应遵循以下格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 具体的响应数据
  }
}
```

### 笔记管理 API

#### POST `/api/notes/upload`

上传笔记图片，进行OCR识别、分类和关键词提取。

**请求**：
```bash
curl -X POST http://localhost:8000/api/notes/upload \
  -F "file=@note.jpg" \
  -F "auto_classify=true" \
  -F "auto_keywords=true"
```

**参数**：
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| file | File | ✅ | 笔记图片 |
| auto_classify | bool | ❌ | 是否自动分类（默认true） |
| auto_keywords | bool | ❌ | 是否提取关键词（默认true） |

**返回**：
```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "id": 1,
    "title": "2026-03-03 笔记",
    "content": "OCR识别的文本...",
    "ocr_confidence": 0.923,
    "category_id": 2,
    "keywords": ["光学", "干涉", "波长"],
    "markdown_path": "data/markdown/物理/1_20260303_120000.md"
  }
}
```

---

#### GET `/api/notes/{note_id}`

获取笔记详情。

**示例**：
```bash
curl http://localhost:8000/api/notes/1
```

**返回**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "2026-03-03 笔记",
    "content": "...",
    "category": {
      "id": 2,
      "name": "物理"
    },
    "keywords": ["光学", "干涉"],
    "created_at": "2026-03-03T12:00:00",
    "is_important": false,
    "status": "published"
  }
}
```

---

#### PUT `/api/notes/{note_id}`

更新笔记信息。

**请求体**：
```json
{
  "title": "新标题",
  "content": "新内容",
  "category_id": 3,
  "keywords": ["新关键词1", "新关键词2"],
  "is_important": true,
  "status": "published"
}
```

---

#### DELETE `/api/notes/{note_id}`

删除笔记及其关联的卡片。

---

### OCR API

#### POST `/api/ocr/process`

单独进行OCR处理（不创建笔记）。

**请求**：
```bash
curl -X POST http://localhost:8000/api/ocr/process \
  -F "file=@image.jpg"
```

**返回**：
```json
{
  "code": 200,
  "message": "处理完成",
  "data": {
    "text": "识别的文本内容...",
    "confidence": 0.923
  }
}
```

---

### 卡片管理 API

#### POST `/api/cards/generate/{note_id}`

根据笔记内容生成复习卡片。

**请求**：
```bash
curl -X POST http://localhost:8000/api/cards/generate/1 \
  -H "Content-Type: application/json" \
  -d '{
    "count": 5,
    "card_types": ["qa", "fill_blank"]
  }'
```

**参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| count | int | 生成的卡片数量（默认5） |
| card_types | List[str] | 卡片类型 |

**返回**：
```json
{
  "code": 200,
  "message": "成功生成 5 张卡片",
  "data": {
    "generated_count": 5,
    "cards": [
      {
        "id": 1,
        "question": "什么是光的干涉？",
        "answer": "两列相干光相遇时发生的现象...",
        "card_type": "qa",
        "difficulty": 3
      }
    ]
  }
}
```

---

#### GET `/api/cards`

获取卡片列表。

**查询参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| note_id | int | 按笔记ID筛选 |
| is_active | bool | 筛选激活状态 |
| page | int | 页码（默认1） |
| page_size | int | 每页数量（默认20） |

---

#### POST `/api/cards/{card_id}/review`

记录卡片复习结果。

**请求体**：
```json
{
  "quality": 4
}
```

**质量等级**：
- 0-2: 遗忘
- 3-4: 模糊
- 5: 完美掌握

---

### 分类管理 API

#### GET `/api/categories`

获取所有分类。

**返回**：
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "物理",
      "description": "物理学相关笔记",
      "keywords": ["光学", "力学", "热学"],
      "color": "#3498db",
      "sort_order": 1
    }
  ]
}
```

---

#### POST `/api/categories`

创建新分类。

**请求体**：
```json
{
  "name": "数学",
  "description": "数学相关笔记",
  "keywords": ["微积分", "线性代数"],
  "color": "#e74c3c"
}
```

---

### 搜索 API

#### GET `/api/search`

全文搜索笔记。

**查询参数**：
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| q | str | ✅ | 搜索关键词 |
| category_id | int | ❌ | 限定分类 |
| date_from | str | ❌ | 开始日期 (YYYY-MM-DD) |
| date_to | str | ❌ | 结束日期 (YYYY-MM-DD) |
| limit | int | ❌ | 结果数量限制（默认50） |

**示例**：
```bash
curl "http://localhost:8000/api/search?q=光学干涉&category_id=2&date_from=2026-03-01"
```

**返回**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "光学干涉实验",
        "highlights": {
          "content": "研究<mark>光学干涉</mark>现象..."
        },
        "category": {
          "id": 2,
          "name": "物理"
        },
        "score": 4.0,
        "created_at": "2026-03-03T12:00:00"
      }
    ],
    "total": 1,
    "query": "光学干涉"
  }
}
```

#### GET `/api/search/suggestions`

获取搜索建议。

**查询参数**：
| 参数 | 说明 |
|------|------|
| q | 部分关键词（最少2个字符） |
| limit | 建议数量（默认10） |

---

## 数据库模式

### ER图

```
┌─────────────────┐
│   categories    │
├─────────────────┤
│ id (PK)         │
│ name (UNIQUE)   │
│ description     │
│ keywords (JSON) │
│ color           │
│ icon            │
│ sort_order      │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1:N
         ↓
┌─────────────────────────┐
│       notes             │
├─────────────────────────┤
│ id (PK)                 │
│ title                   │
│ content                 │
│ clean_content           │
│ image_path              │
│ markdown_path           │
│ category_id (FK)        │
│ keywords (JSON)         │
│ is_important            │
│ status                  │
│ ocr_confidence          │
│ source                  │
│ extra_data (JSON)       │
│ created_at              │
│ updated_at              │
└────────┬────────────────┘
         │
         │ 1:N
         ↓
┌────────────────────────┐
│   review_cards         │
├────────────────────────┤
│ id (PK)                │
│ note_id (FK)           │
│ question               │
│ answer                 │
│ card_type              │
│ difficulty             │
│ next_review            │
│ interval               │
│ ease_factor            │
│ review_count           │
│ correct_count          │
│ last_review            │
│ is_active              │
│ created_at             │
│ updated_at             │
└────────┬───────────────┘
         │
         │ 1:N
         ↓
┌────────────────────────┐
│   review_logs          │
├────────────────────────┤
│ id (PK)                │
│ card_id (FK)           │
│ quality (0-5)          │
│ reviewed_at            │
│ time_spent (seconds)   │
│ created_at             │
│ updated_at             │
└────────────────────────┘
```

### SQL Schema

```sql
-- 分类表
CREATE TABLE categories (
  id INTEGER PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,
  description TEXT,
  keywords TEXT DEFAULT '[]',
  color VARCHAR(7) DEFAULT '#3498db',
  icon VARCHAR(50),
  sort_order INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 笔记表
CREATE TABLE notes (
  id INTEGER PRIMARY KEY,
  title VARCHAR(200),
  content TEXT,
  clean_content TEXT,
  image_path VARCHAR(500) NOT NULL,
  markdown_path VARCHAR(500),
  category_id INTEGER,
  keywords TEXT DEFAULT '[]',
  is_important BOOLEAN DEFAULT 0,
  status VARCHAR(20) DEFAULT 'draft',
  ocr_confidence FLOAT,
  source VARCHAR(50) DEFAULT 'upload',
  extra_data TEXT DEFAULT '{}',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- 复习卡片表
CREATE TABLE review_cards (
  id INTEGER PRIMARY KEY,
  note_id INTEGER NOT NULL,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  card_type VARCHAR(20) DEFAULT 'qa',
  difficulty INTEGER DEFAULT 3,
  next_review DATETIME,
  interval INTEGER DEFAULT 1,
  ease_factor FLOAT DEFAULT 2.5,
  review_count INTEGER DEFAULT 0,
  correct_count INTEGER DEFAULT 0,
  last_review DATETIME,
  is_active BOOLEAN DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);

-- 复习日志表
CREATE TABLE review_logs (
  id INTEGER PRIMARY KEY,
  card_id INTEGER NOT NULL,
  quality INTEGER NOT NULL,
  reviewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  time_spent INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (card_id) REFERENCES review_cards(id) ON DELETE CASCADE
);
```

---

## 常见问题

**Q: 如何更换为PostgreSQL？**
A: 更新 `.env` 中的 `DATABASE_URL`：
```
DATABASE_URL=postgresql://user:password@localhost:5432/note_organizer
```
然后重新初始化数据库。

**Q: OCR识别效果不好？**
A: 可以尝试：
1. 确保图片清晰、光线充足
2. 启用AI优化：设置 `AI_REFINE_OCR=true`
3. 检查 `OCR_LANG` 配置是否正确

**Q: 如何禁用GPU加速？**
A: 在 `.env` 中设置：
```
STRUCTURE_DEVICE=cpu
```

**Q: 卡片生成失败怎么办？**
A: 检查：
1. OpenAI API Key是否正确
2. API额度是否充足
3. 网络连接是否正常

---

## 许可证

[待补充]

## 贡献

欢迎提交Issue和Pull Request！

---

## 更新日志

### v1.0.0 (2026-03-03)

- ✅ 核心功能完成
- ✅ API接口完成
- ✅ OCR和结构识别
- ✅ AI卡片生成
- ✅ 搜索功能

---

**最后更新**：2026年3月3日
