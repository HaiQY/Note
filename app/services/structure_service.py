from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.config import IMAGES_DIR
from app.logger import logger


@dataclass
class StructureResult:
    text: str
    markdown: str
    confidence: float
    formula_count: int = 0
    table_count: int = 0
    image_regions: List[Dict[str, Any]] = field(default_factory=list)
    formula_regions: List[Dict[str, Any]] = field(default_factory=list)
    table_regions: List[Dict[str, Any]] = field(default_factory=list)
    diagram_regions: List[Dict[str, Any]] = field(default_factory=list)


class StructureService:
    _instance = None
    _pipeline = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if StructureService._pipeline is None:
            self._init_pipeline()
    
    def _init_pipeline(self):
        try:
            from paddleocr import PPStructureV3
            
            StructureService._pipeline = PPStructureV3(
                use_formula_recognition=True,
                use_table_recognition=True,
                use_chart_recognition=False,
                use_seal_recognition=False,
                use_doc_orientation_classify=False,
                use_textline_orientation=True,
                use_doc_unwarping=False,
                device="gpu" if self._check_gpu() else "cpu"
            )
            
        except ImportError:
            logger.warning("PPStructureV3 not installed. Structure service will use fallback.")
            StructureService._pipeline = None
        except Exception as e:
            logger.warning(f"Failed to initialize PPStructureV3: {e}")
            StructureService._pipeline = None
    
    def _check_gpu(self) -> bool:
        try:
            import paddle
            return paddle.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0
        except Exception:
            return False
    
    def process_image(self, image_path: str, save_images_dir: Optional[str] = None) -> StructureResult:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        if StructureService._pipeline is None:
            return self._fallback_result(image_path)
        
        try:
            output = StructureService._pipeline.predict(str(path))
            
            if not output:
                return StructureResult(text="", markdown="", confidence=0.0)
            
            res = output[0]
            
            res_data = res['res'] if isinstance(res, dict) and 'res' in res else res
            
            text_parts = []
            formula_regions = []
            table_regions = []
            image_regions = []
            diagram_regions = []
            
            if hasattr(res, 'markdown'):
                md_info = res.markdown
            elif isinstance(res, dict):
                md_info = res.get('markdown', {})
            else:
                md_info = {}
            
            markdown_text = ""
            if isinstance(md_info, dict):
                markdown_text = md_info.get('markdown_texts', '')
            
            overall_ocr = {}
            if hasattr(res_data, 'get'):
                overall_ocr = res_data.get('overall_ocr_res', {})
            elif isinstance(res_data, dict):
                overall_ocr = res_data.get('overall_ocr_res', {})
            
            rec_texts = []
            rec_scores = []
            if isinstance(overall_ocr, dict):
                rec_texts = overall_ocr.get('rec_texts', [])
                rec_scores = overall_ocr.get('rec_scores', [])
            
            avg_confidence = sum(rec_scores) / len(rec_scores) if rec_scores else 0.9
            
            if rec_texts:
                full_text = '\n'.join(rec_texts)
            else:
                parsing_list = []
                if hasattr(res_data, 'get'):
                    parsing_list = res_data.get('parsing_res_list', [])
                elif isinstance(res_data, dict):
                    parsing_list = res_data.get('parsing_res_list', [])
                
                for item in parsing_list:
                    if isinstance(item, dict):
                        block_label = item.get('block_label', '')
                        block_content = item.get('block_content', '')
                        
                        if block_label in ['text', 'title', 'header', 'footer']:
                            if block_content:
                                text_parts.append(block_content)
                        elif block_label == 'image':
                            image_regions.append({
                                'content': block_content,
                                'bbox': item.get('block_bbox', [])
                            })
                        elif block_label == 'chart':
                            diagram_regions.append({
                                'content': block_content,
                                'bbox': item.get('block_bbox', [])
                            })
                
                full_text = '\n\n'.join(text_parts)
            
            formula_res_list = []
            if hasattr(res_data, 'get'):
                formula_res_list = res_data.get('formula_res_list', [])
            elif isinstance(res_data, dict):
                formula_res_list = res_data.get('formula_res_list', [])
            
            for formula in formula_res_list:
                if isinstance(formula, dict):
                    formula_text = formula.get('rec_formula', '')
                    if formula_text:
                        formula_regions.append({
                            'latex': formula_text,
                            'bbox': self._convert_bbox(formula.get('rec_polys'))
                        })
            
            table_res_list = []
            if hasattr(res_data, 'get'):
                table_res_list = res_data.get('table_res_list', [])
            elif isinstance(res_data, dict):
                table_res_list = res_data.get('table_res_list', [])
            
            for table in table_res_list:
                if isinstance(table, dict):
                    pred_html = table.get('pred_html', '')
                    if pred_html:
                        table_regions.append({
                            'html': pred_html,
                            'bbox': table.get('cell_box_list', [])
                        })
            
            return StructureResult(
                text=full_text,
                markdown=markdown_text,
                confidence=avg_confidence,
                formula_count=len(formula_regions),
                table_count=len(table_regions),
                image_regions=image_regions,
                formula_regions=formula_regions,
                table_regions=table_regions,
                diagram_regions=diagram_regions
            )
            
        except Exception as e:
            import traceback
            logger.error(f"Structure processing failed: {e}")
            traceback.print_exc()
            return self._fallback_result(image_path)
    
    def _convert_bbox(self, bbox):
        if bbox is None:
            return []
        if isinstance(bbox, np.ndarray):
            return bbox.tolist()
        return bbox
    
    def process_image_bytes(self, image_bytes: bytes, save_images_dir: Optional[str] = None) -> StructureResult:
        if StructureService._pipeline is None:
            return StructureResult(
                text="[模拟结果] PPStructureV3 未安装",
                markdown="",
                confidence=0.0
            )
        
        try:
            import cv2
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            output = StructureService._pipeline.predict(img)
            
            if not output:
                return StructureResult(text="", markdown="", confidence=0.0)
            
            res = output[0]
            
            res_data = res['res'] if isinstance(res, dict) and 'res' in res else res
            
            text_parts = []
            formula_regions = []
            table_regions = []
            image_regions = []
            diagram_regions = []
            
            if hasattr(res, 'markdown'):
                md_info = res.markdown
            elif isinstance(res, dict):
                md_info = res.get('markdown', {})
            else:
                md_info = {}
            
            markdown_text = ""
            if isinstance(md_info, dict):
                markdown_text = md_info.get('markdown_texts', '')
            
            overall_ocr = {}
            if hasattr(res_data, 'get'):
                overall_ocr = res_data.get('overall_ocr_res', {})
            elif isinstance(res_data, dict):
                overall_ocr = res_data.get('overall_ocr_res', {})
            
            rec_texts = []
            rec_scores = []
            if isinstance(overall_ocr, dict):
                rec_texts = overall_ocr.get('rec_texts', [])
                rec_scores = overall_ocr.get('rec_scores', [])
            
            avg_confidence = sum(rec_scores) / len(rec_scores) if rec_scores else 0.9
            
            if rec_texts:
                full_text = '\n'.join(rec_texts)
            else:
                full_text = ""
            
            return StructureResult(
                text=full_text,
                markdown=markdown_text,
                confidence=avg_confidence,
                formula_count=len(formula_regions),
                table_count=len(table_regions),
                image_regions=image_regions,
                formula_regions=formula_regions,
                table_regions=table_regions,
                diagram_regions=diagram_regions
            )
            
        except Exception as e:
            import traceback
            logger.error(f"Structure processing failed: {e}")
            traceback.print_exc()
            return StructureResult(text="", markdown="", confidence=0.0)
    
    def _fallback_result(self, image_path: str) -> StructureResult:
        return StructureResult(
            text=f"[模拟结果] 图片 {Path(image_path).name} 的结构化解析内容。",
            markdown=f"# 模拟结果\n\n这是 {Path(image_path).name} 的模拟输出。",
            confidence=0.95
        )
    
    def extract_diagram_structure(self, image_path: str) -> Dict[str, Any]:
        if StructureService._pipeline is None:
            return {"nodes": [], "edges": [], "type": "unknown"}
        
        try:
            import cv2
            img = cv2.imread(image_path)
            if img is None:
                return {"nodes": [], "edges": [], "type": "unknown"}
            
            output = StructureService._pipeline.predict(img)
            if not output:
                return {"nodes": [], "edges": [], "type": "unknown"}
            
            res = output[0]
            res_data = res['res'] if isinstance(res, dict) and 'res' in res else res
            
            overall_ocr = {}
            if hasattr(res_data, 'get'):
                overall_ocr = res_data.get('overall_ocr_res', {})
            elif isinstance(res_data, dict):
                overall_ocr = res_data.get('overall_ocr_res', {})
            
            rec_texts = []
            rec_polys = []
            if isinstance(overall_ocr, dict):
                rec_texts = overall_ocr.get('rec_texts', [])
                rec_polys = overall_ocr.get('rec_polys', [])
            
            if not rec_texts:
                return {"nodes": [], "edges": [], "type": "unknown"}
            
            nodes = []
            for i, (text, poly) in enumerate(zip(rec_texts, rec_polys)):
                if isinstance(poly, np.ndarray):
                    points = poly.tolist()
                else:
                    points = poly
                
                if points and len(points) >= 4:
                    x_coords = [p[0] for p in points]
                    y_coords = [p[1] for p in points]
                    center_x = sum(x_coords) / len(x_coords)
                    center_y = sum(y_coords) / len(y_coords)
                    width = max(x_coords) - min(x_coords)
                    height = max(y_coords) - min(y_coords)
                else:
                    center_x, center_y, width, height = 0, 0, 0, 0
                
                nodes.append({
                    'id': i,
                    'text': text,
                    'x': center_x,
                    'y': center_y,
                    'width': width,
                    'height': height
                })
            
            edges = self._infer_edges(nodes)
            diagram_type = self._detect_diagram_type(nodes, edges)
            
            return {
                "nodes": nodes,
                "edges": edges,
                "type": diagram_type
            }
            
        except Exception as e:
            logger.error(f"Diagram structure extraction failed: {e}")
            return {"nodes": [], "edges": [], "type": "unknown"}
    
    def _infer_edges(self, nodes: List[Dict]) -> List[Dict]:
        edges = []
        
        if len(nodes) < 2:
            return edges
        
        sorted_nodes = sorted(nodes, key=lambda n: (n['y'], n['x']))
        
        for i, node in enumerate(sorted_nodes):
            candidates = []
            for j, other in enumerate(sorted_nodes):
                if i == j:
                    continue
                
                dx = other['x'] - node['x']
                dy = other['y'] - node['y']
                
                if dy > 0 and dy < node['height'] * 3:
                    if abs(dx) < node['width'] * 2:
                        candidates.append((j, dy, abs(dx)))
            
            if candidates:
                candidates.sort(key=lambda c: (c[1], c[2]))
                edges.append({
                    'from': node['id'],
                    'to': candidates[0][0]
                })
        
        return edges
    
    def _detect_diagram_type(self, nodes: List[Dict], edges: List[Dict]) -> str:
        if not edges:
            return "unknown"
        
        has_vertical = False
        has_horizontal = False
        
        for edge in edges:
            from_node = next((n for n in nodes if n['id'] == edge['from']), None)
            to_node = next((n for n in nodes if n['id'] == edge['to']), None)
            
            if from_node and to_node:
                dx = abs(to_node['x'] - from_node['x'])
                dy = abs(to_node['y'] - from_node['y'])
                
                if dy > dx:
                    has_vertical = True
                else:
                    has_horizontal = True
        
        if has_vertical and not has_horizontal:
            return "flowchart"
        elif has_horizontal and not has_vertical:
            return "timeline"
        elif has_vertical and has_horizontal:
            return "mindmap"
        else:
            return "unknown"
    
    def generate_mermaid(self, structure: Dict[str, Any]) -> str:
        diagram_type = structure.get('type', 'unknown')
        nodes = structure.get('nodes', [])
        edges = structure.get('edges', [])
        
        if not nodes:
            return ""
        
        lines = []
        
        if diagram_type == "flowchart":
            lines.append("```mermaid")
            lines.append("flowchart TD")
        elif diagram_type == "mindmap":
            lines.append("```mermaid")
            lines.append("mindmap")
        else:
            lines.append("```mermaid")
            lines.append("flowchart TD")
        
        node_definitions = {}
        for node in nodes:
            node_id = f"N{node['id']}"
            text = node['text'].replace('"', "'")
            node_definitions[node['id']] = node_id
            lines.append(f'    {node_id}["{text}"]')
        
        for edge in edges:
            from_id = node_definitions.get(edge['from'])
            to_id = node_definitions.get(edge['to'])
            if from_id and to_id:
                lines.append(f'    {from_id} --> {to_id}')
        
        lines.append("```")
        
        return '\n'.join(lines)