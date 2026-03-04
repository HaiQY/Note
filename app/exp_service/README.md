# 实验性 Embedding 分类模块

> 基于 BGE-small-zh-v1.5 的语义分类实验

本模块是一个实验性的笔记分类方案，使用 Embedding 模型计算文本语义相似度，与现有的关键词匹配方法进行对比研究。

## 目录结构

```
app/exp_service/
├── __init__.py                # 模块导出
├── config.py                  # 配置（模型名称、维度、分类描述）
├── embedding_classifier.py    # Embedding 分类器核心实现
├── category_embeddings.py     # 分类向量预计算与缓存管理
├── benchmark.py               # 对比基准测试脚本
└── README.md                  # 本文档
```

## 依赖安装

```bash
pip install sentence-transformers>=2.2.0
```

首次运行时，模型会自动从 HuggingFace 下载（约 100MB）。

## 使用方法

### 1. 作为分类器使用

```python
from sqlalchemy.orm import Session
from app.exp_service import EmbeddingClassifier

# 初始化分类器
classifier = EmbeddingClassifier()

# 检查模型是否可用
if classifier.is_available():
    # 初始化分类（预计算分类向量）
    classifier.init_categories(db)
    
    # 分类文本
    category, score = classifier.classify("这是一段物理笔记内容...", db)
    print(f"分类结果: {category.name}, 置信度: {score:.3f}")
```

### 2. 运行基准测试

```bash
cd /path/to/Note
python -m app.exp_service.benchmark
```

测试结果将保存在 `data/benchmark/` 目录下：
- `benchmark_results_*.json` - 详细测试结果
- `benchmark_summary_*.json` - 汇总统计
- `benchmark_report_*.md` - Markdown 格式报告

## 算法原理

### 零样本分类 (Zero-shot Classification)

```
输入文本 → Embedding模型 → 文本向量 (768维)
                        ↓
预计算分类向量 ───────→ 余弦相似度计算
                        ↓
                    选择最高分分类
```

### 分类向量构建

每个分类的向量由以下内容编码生成：
1. 分类名称（如"物理"）
2. 分类描述（预定义的语义描述）
3. 分类关键词（从数据库读取）

```
分类向量 = Embedding("分类：物理。物理学相关内容，包括力学、电磁学... 相关关键词：运动、力、能量...")
```

## 对比分析

| 维度 | 关键词匹配 | Embedding 分类 |
|------|------------|----------------|
| **原理** | 关键词命中计数 | 语义向量相似度 |
| **速度** | 快 (O(n×m)) | 较慢 (首次加载模型) |
| **准确率** | 依赖关键词覆盖 | 依赖语义理解 |
| **泛化能力** | 弱（需同义词扩展） | 强（语义相似即可） |
| **可解释性** | 高（可见匹配词） | 低（黑盒语义） |
| **新增分类** | 需定义关键词 | 仅需描述文本 |
| **资源需求** | 内存级 | 模型加载 (~400MB) |

## 边界情况测试

基准测试包含以下边界情况样本：

1. **跨学科内容**
   - "物理中的数学方法" → 测试语义偏向
   - "化学反应中的能量变化" → 物理/化学边界

2. **短文本**
   - 只有 1-2 句话的笔记

3. **专业术语密集**
   - 大量生僻专业词汇

4. **混合语言**
   - 中英文混合内容

## 配置说明

编辑 `config.py` 修改配置：

```python
# 模型配置
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"  # 模型名称
EMBEDDING_DIM = 768                               # 向量维度

# 分类阈值
DEFAULT_THRESHOLD = 0.3  # 低于此值归为"其他"

# 分类描述（可扩展）
CATEGORY_DESCRIPTIONS = {
    "数学": "数学相关内容，包括...",
    # ...
}
```

## 扩展分类

添加新分类时，只需在 `config.py` 的 `CATEGORY_DESCRIPTIONS` 中添加描述：

```python
CATEGORY_DESCRIPTIONS["新分类名"] = "该分类的详细描述，包含核心概念和关键词..."
```

## 报告集成

本模块的测试结果可直接用于研究报告：

1. 运行 `benchmark.py` 生成报告
2. 报告自动保存为 Markdown 格式
3. 包含准确率、耗时、一致性分析等指标

---

