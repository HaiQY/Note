import json
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.dao.category_dao import CategoryDAO
from app.dao.note_dao import NoteDAO
from app.services.classify_service import ClassifyService
from app.exp_service.embedding_classifier import EmbeddingClassifier
from app.logger import logger


@dataclass
class BenchmarkResult:
    note_id: int
    note_title: str
    true_category: str
    keyword_category: str
    keyword_score: float
    keyword_time_ms: float
    embedding_category: str
    embedding_score: float
    embedding_time_ms: float
    keyword_correct: bool
    embedding_correct: bool


@dataclass
class BenchmarkSummary:
    total_notes: int
    keyword_accuracy: float
    embedding_accuracy: float
    keyword_avg_time_ms: float
    embedding_avg_time_ms: float
    keyword_correct_count: int
    embedding_correct_count: int
    both_correct: int
    both_wrong: int
    keyword_only_correct: int
    embedding_only_correct: int
    timestamp: str


TEST_DATASET = [
    {"content": "牛顿第二定律表明物体的加速度与作用力成正比，与质量成反比。公式F=ma是力学的基础。", "expected": "物理"},
    {"content": "二次函数的一般形式是y=ax²+bx+c，其中a≠0。其图像是一条抛物线。", "expected": "数学"},
    {"content": "水的分子式是H₂O，由两个氢原子和一个氧原子组成。水是生命之源。", "expected": "化学"},
    {"content": "The present perfect tense is formed with have/has + past participle. It describes actions that happened at an unspecified time.", "expected": "英语"},
    {"content": "Python中的列表推导式提供了一种简洁的方式来创建列表。例如[x**2 for x in range(10)]。", "expected": "编程"},
    {"content": "《静夜思》是唐代诗人李白的名作：床前明月光，疑是地上霜。举头望明月，低头思故乡。", "expected": "语文"},
    {"content": "秦始皇统一六国，建立了中国历史上第一个中央集权的封建王朝。公元前221年完成统一。", "expected": "历史"},
    {"content": "长江是中国最长的河流，全长6300多公里，发源于青藏高原，注入东海。", "expected": "地理"},
    {"content": "细胞是生物体结构和功能的基本单位。细胞膜、细胞质和细胞核是细胞的主要组成部分。", "expected": "生物"},
    {"content": "宪法是国家的根本大法，具有最高的法律效力。一切法律、法规都不得与宪法相抵触。", "expected": "政治"},
    {"content": "光的干涉现象说明光具有波动性。两列相干光波相遇时会产生明暗相间的干涉条纹。", "expected": "物理"},
    {"content": "导数是函数在某一点处的变化率。函数f(x)在x₀处的导数定义为极限lim(Δx→0) [f(x₀+Δx)-f(x₀)]/Δx。", "expected": "数学"},
    {"content": "氧化还原反应的本质是电子的转移。失去电子的物质被氧化，得到电子的物质被还原。", "expected": "化学"},
    {"content": "Relative clauses provide additional information about a noun. They can be defining or non-defining.", "expected": "英语"},
    {"content": "React是一个用于构建用户界面的JavaScript库。它采用组件化开发和虚拟DOM技术。", "expected": "编程"},
    {"content": "比喻是一种修辞手法，通过两种不同性质的事物之间的相似点来描写事物。", "expected": "语文"},
    {"content": "文艺复兴起源于14世纪的意大利，是一场思想文化运动，强调人文主义精神。", "expected": "历史"},
    {"content": "季风是由于海陆热力性质差异而形成的大范围盛行风向随季节变化的现象。", "expected": "地理"},
    {"content": "DNA双螺旋结构由沃森和克里克发现。DNA是遗传信息的载体，由四种碱基组成。", "expected": "生物"},
    {"content": "市场经济是通过市场配置资源的经济形式。价格机制、供求机制和竞争机制是其核心。", "expected": "政治"},
    {"content": "热力学第一定律是能量守恒定律在热学中的表达：系统内能的变化等于热量与功的代数和。", "expected": "物理"},
    {"content": "行列式是方阵的一个标量值，记作det(A)或|A|。它在解线性方程组中有重要应用。", "expected": "数学"},
    {"content": "酯化反应是酸和醇作用生成酯和水的反应。乙酸和乙醇反应生成乙酸乙酯。", "expected": "化学"},
    {"content": "Phrasal verbs are combinations of verbs and particles. They often have idiomatic meanings.", "expected": "英语"},
    {"content": "SQL是结构化查询语言，用于管理关系数据库。SELECT语句用于查询数据。", "expected": "编程"},
    {"content": "鲁迅是中国现代文学的奠基人，代表作有《狂人日记》《阿Q正传》等。", "expected": "语文"},
    {"content": "第一次世界大战爆发于1914年，导火索是萨拉热窝事件。战争持续了四年。", "expected": "历史"},
    {"content": "板块构造学说认为地球表层由若干板块组成，板块运动导致地震、火山等地质现象。", "expected": "地理"},
    {"content": "光合作用是绿色植物利用光能将二氧化碳和水转化为有机物并释放氧气的过程。", "expected": "生物"},
    {"content": "价值规律是商品经济的基本规律，商品的价值量由社会必要劳动时间决定。", "expected": "政治"},
    {"content": "电磁感应现象由法拉第发现，变化的磁场在导体中产生感应电动势。", "expected": "物理"},
    {"content": "级数是将数列的各项依次相加得到的表达式。收敛级数的部分和有极限。", "expected": "数学"},
    {"content": "电解质是在水溶液中或熔融状态下能导电的化合物，如氯化钠、硫酸等。", "expected": "化学"},
    {"content": "Conditionals express hypothetical situations. Zero conditional describes general truths.", "expected": "英语"},
    {"content": "Git是分布式版本控制系统，用于跟踪代码变更。常用命令有commit、push、pull等。", "expected": "编程"},
    {"content": "唐诗是中国古典诗歌的巅峰，李白和杜甫是最杰出的代表诗人。", "expected": "语文"},
    {"content": "丝绸之路是古代连接东西方的贸易通道，因运输丝绸而得名。张骞开辟了这条道路。", "expected": "历史"},
    {"content": "温室效应是指大气中的温室气体吸收地表辐射的热量，使地球表面温度升高的现象。", "expected": "地理"},
    {"content": "基因突变是指DNA分子中碱基对的增添、缺失或替换，是生物变异的根本来源。", "expected": "生物"},
    {"content": "社会主义核心价值观包括富强、民主、文明、和谐、自由、平等、公正、法治等。", "expected": "政治"},
    {"content": "相对论由爱因斯坦提出，分为狭义相对论和广义相对论，彻底改变了时空观念。", "expected": "物理"},
    {"content": "概率论研究随机现象的规律性。事件的概率是衡量其发生可能性大小的数值。", "expected": "数学"},
    {"content": "有机高分子化合物是由大量单体通过聚合反应形成的大分子，如聚乙烯、蛋白质等。", "expected": "化学"},
    {"content": "Reported speech is used to convey what someone else said without using their exact words.", "expected": "英语"},
    {"content": "Docker是一种容器化技术，可以将应用程序及其依赖打包成可移植的容器。", "expected": "编程"},
    {"content": "宋词是宋代的主要文学形式，分为婉约派和豪放派，苏轼、辛弃疾是豪放派代表。", "expected": "语文"},
    {"content": "工业革命始于18世纪的英国，蒸汽机的发明推动了机器大工业时代的到来。", "expected": "历史"},
    {"content": "洋流是海洋中大规模的海水运动，分为暖流和寒流，对气候有重要影响。", "expected": "地理"},
    {"content": "减数分裂是有性生殖生物产生生殖细胞的过程，染色体数目减半。", "expected": "生物"},
]


class Benchmark:
    def __init__(self, db: Session):
        self.db = db
        self.keyword_classifier = ClassifyService(db)
        self.embedding_classifier = EmbeddingClassifier()
        
        if self.embedding_classifier.is_available():
            self.embedding_classifier.init_categories(db)
    
    def run_single_test(self, content: str, expected_category: str) -> BenchmarkResult:
        note_title = content[:30] + "..." if len(content) > 30 else content
        
        kw_start = time.perf_counter()
        kw_category = self.keyword_classifier.classify(content)
        kw_time = (time.perf_counter() - kw_start) * 1000
        kw_score = 0.0
        
        emb_start = time.perf_counter()
        emb_category, emb_score = self.embedding_classifier.classify(content, self.db)
        emb_time = (time.perf_counter() - emb_start) * 1000
        
        kw_cat_name = kw_category.name if kw_category else "None"
        emb_cat_name = emb_category.name if emb_category else "None"
        
        return BenchmarkResult(
            note_id=0,
            note_title=note_title,
            true_category=expected_category,
            keyword_category=kw_cat_name,
            keyword_score=kw_score,
            keyword_time_ms=kw_time,
            embedding_category=emb_cat_name,
            embedding_score=emb_score,
            embedding_time_ms=emb_time,
            keyword_correct=kw_cat_name == expected_category,
            embedding_correct=emb_cat_name == expected_category,
        )
    
    def run_benchmark(self, test_data: List[Dict] = None) -> Tuple[List[BenchmarkResult], BenchmarkSummary]:
        if test_data is None:
            test_data = TEST_DATASET
        
        results = []
        
        for i, item in enumerate(test_data):
            result = self.run_single_test(item["content"], item["expected"])
            result.note_id = i + 1
            results.append(result)
            logger.info(f"Test {i+1}/{len(test_data)}: Expected={item['expected']}, "
                       f"Keyword={result.keyword_category}, Embedding={result.embedding_category}")
        
        summary = self._compute_summary(results)
        return results, summary
    
    def _compute_summary(self, results: List[BenchmarkResult]) -> BenchmarkSummary:
        total = len(results)
        kw_correct = sum(1 for r in results if r.keyword_correct)
        emb_correct = sum(1 for r in results if r.embedding_correct)
        
        kw_avg_time = sum(r.keyword_time_ms for r in results) / total if total > 0 else 0
        emb_avg_time = sum(r.embedding_time_ms for r in results) / total if total > 0 else 0
        
        both_correct = sum(1 for r in results if r.keyword_correct and r.embedding_correct)
        both_wrong = sum(1 for r in results if not r.keyword_correct and not r.embedding_correct)
        kw_only = sum(1 for r in results if r.keyword_correct and not r.embedding_correct)
        emb_only = sum(1 for r in results if not r.keyword_correct and r.embedding_correct)
        
        return BenchmarkSummary(
            total_notes=total,
            keyword_accuracy=kw_correct / total * 100 if total > 0 else 0,
            embedding_accuracy=emb_correct / total * 100 if total > 0 else 0,
            keyword_avg_time_ms=kw_avg_time,
            embedding_avg_time_ms=emb_avg_time,
            keyword_correct_count=kw_correct,
            embedding_correct_count=emb_correct,
            both_correct=both_correct,
            both_wrong=both_wrong,
            keyword_only_correct=kw_only,
            embedding_only_correct=emb_only,
            timestamp=datetime.now().isoformat(),
        )
    
    def save_results(self, results: List[BenchmarkResult], summary: BenchmarkSummary, output_dir: str = "data/benchmark"):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results_file = output_path / f"benchmark_results_{timestamp}.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in results], f, ensure_ascii=False, indent=2)
        
        summary_file = output_path / f"benchmark_summary_{timestamp}.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(asdict(summary), f, ensure_ascii=False, indent=2)
        
        report_file = output_path / f"benchmark_report_{timestamp}.md"
        self._generate_report(results, summary, report_file)
        
        logger.info(f"Benchmark results saved to {output_path}")
        return results_file, summary_file, report_file
    
    def _generate_report(self, results: List[BenchmarkResult], summary: BenchmarkSummary, output_file: Path):
        report_lines = [
            "# 分类算法对比基准测试报告",
            "",
            f"**测试时间**: {summary.timestamp}",
            f"**测试样本数**: {summary.total_notes}",
            "",
            "## 一、总体对比",
            "",
            "| 指标 | 关键词匹配 | Embedding分类 |",
            "|------|------------|---------------|",
            f"| **准确率** | {summary.keyword_accuracy:.2f}% | {summary.embedding_accuracy:.2f}% |",
            f"| **正确数** | {summary.keyword_correct_count}/{summary.total_notes} | {summary.embedding_correct_count}/{summary.total_notes} |",
            f"| **平均耗时** | {summary.keyword_avg_time_ms:.2f}ms | {summary.embedding_avg_time_ms:.2f}ms |",
            "",
            "## 二、一致性分析",
            "",
            f"- 两者都正确: {summary.both_correct} ({summary.both_correct/summary.total_notes*100:.1f}%)",
            f"- 两者都错误: {summary.both_wrong} ({summary.both_wrong/summary.total_notes*100:.1f}%)",
            f"- 仅关键词正确: {summary.keyword_only_correct}",
            f"- 仅Embedding正确: {summary.embedding_only_correct}",
            "",
            "## 三、详细结果",
            "",
            "| 序号 | 预期分类 | 关键词分类 | Embedding分类 | 关键词正确 | Embedding正确 |",
            "|------|----------|------------|---------------|------------|---------------|",
        ]
        
        for r in results:
            report_lines.append(
                f"| {r.note_id} | {r.true_category} | {r.keyword_category} | "
                f"{r.embedding_category} | {'✓' if r.keyword_correct else '✗'} | "
                f"{'✓' if r.embedding_correct else '✗'} |"
            )
        
        report_lines.extend([
            "",
            "## 四、方法分析",
            "",
            "### 关键词匹配方法",
            "- **优点**: 速度快、可解释性强、无需模型加载",
            "- **缺点**: 依赖关键词覆盖度、对同义词泛化能力弱",
            "",
            "### Embedding分类方法",
            "- **优点**: 语义理解能力强、泛化性好、无需预定义关键词",
            "- **缺点**: 需要模型加载、首次运行较慢、可解释性弱",
            "",
            "## 五、结论",
            "",
        ])
        
        if summary.keyword_accuracy > summary.embedding_accuracy:
            report_lines.append("在当前测试集上，关键词匹配方法的准确率更高。建议保持使用关键词匹配作为主要分类方法。")
        elif summary.embedding_accuracy > summary.keyword_accuracy:
            report_lines.append("在当前测试集上，Embedding分类方法的准确率更高。可考虑将其作为主要分类方法或辅助方法。")
        else:
            report_lines.append("两种方法的准确率相近。可根据具体场景选择：追求速度用关键词匹配，追求语义理解用Embedding分类。")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))


def run_benchmark():
    db = SessionLocal()
    try:
        benchmark = Benchmark(db)
        results, summary = benchmark.run_benchmark()
        
        print("\n" + "="*60)
        print("分类算法对比基准测试结果")
        print("="*60)
        print(f"测试样本数: {summary.total_notes}")
        print(f"关键词匹配准确率: {summary.keyword_accuracy:.2f}%")
        print(f"Embedding分类准确率: {summary.embedding_accuracy:.2f}%")
        print(f"关键词匹配平均耗时: {summary.keyword_avg_time_ms:.2f}ms")
        print(f"Embedding分类平均耗时: {summary.embedding_avg_time_ms:.2f}ms")
        print("="*60)
        
        results_file, summary_file, report_file = benchmark.save_results(results, summary)
        print(f"\n结果已保存:")
        print(f"  - {results_file}")
        print(f"  - {summary_file}")
        print(f"  - {report_file}")
        
        return results, summary
    finally:
        db.close()


if __name__ == "__main__":
    run_benchmark()