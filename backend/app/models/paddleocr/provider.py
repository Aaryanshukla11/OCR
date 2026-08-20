import os
import time
import numpy as np
from typing import List, Dict, Any
from app.models.base.provider import BaseOCRProvider

# Set environment flags BEFORE importing paddle
os.environ['FLAGS_use_onednn'] = '0'
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_enable_onednn'] = '0'
os.environ['PADDLE_DISABLE_ONEDNN'] = '1'
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

class PaddleOCRProvider(BaseOCRProvider):
    _instance = None
    
    @classmethod
    def get_instance(cls, lang: str = "en"):
        if cls._instance is None:
            cls._instance = cls(lang=lang)
        return cls._instance

    def __init__(self, lang: str = "en"):
        print(f"Initializing PaddleOCR Provider (lang={lang})...")
        import paddle
        from paddleocr import PaddleOCR
        
        self.paddle = paddle
        self._device = "GPU" if paddle.is_compiled_with_cuda() and paddle.device.get_device().startswith("gpu") else "CPU"
        print(f"PaddleOCR Provider active on device: {self._device}")
        
        t0 = time.time()
        try:
            self.ocr = PaddleOCR(lang=lang, enable_mkldnn=False)
        except Exception:
            try:
                self.ocr = PaddleOCR(use_textline_orientation=True, lang=lang)
            except Exception:
                self.ocr = PaddleOCR(lang=lang)
                
        init_dur = time.time() - t0
        print(f"PaddleOCR models loaded in {init_dur:.2f}s")

    @property
    def provider_name(self) -> str:
        return "PaddleOCR"

    @property
    def device(self) -> str:
        return self._device

    def _parse_paddle_output(self, raw_output) -> List[Dict[str, Any]]:
        regions = []
        if not raw_output:
            return regions
            
        # Format A: Paddlex 3.x dict format (list of dicts)
        if isinstance(raw_output, list) and len(raw_output) > 0 and isinstance(raw_output[0], dict):
            page_data = raw_output[0]
            texts = page_data.get('rec_texts', [])
            scores = page_data.get('rec_scores', [])
            polys = page_data.get('rec_polys') if page_data.get('rec_polys') is not None else page_data.get('dt_polys', [])
            boxes = page_data.get('rec_boxes', [])
            
            for idx, text in enumerate(texts):
                score = float(scores[idx]) if idx < len(scores) else 0.0
                
                poly_coords = []
                if polys is not None and idx < len(polys):
                    p = polys[idx]
                    if hasattr(p, 'tolist'):
                        poly_coords = p.tolist()
                    elif isinstance(p, (list, tuple)):
                        poly_coords = [list(pt) for pt in p]
                        
                if not poly_coords and idx < len(boxes):
                    b = boxes[idx]
                    if hasattr(b, 'tolist'):
                        b = b.tolist()
                    poly_coords = [
                        [b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]]
                    ]
                    
                if poly_coords:
                    xs = [pt[0] for pt in poly_coords]
                    ys = [pt[1] for pt in poly_coords]
                    bbox = [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))]
                else:
                    bbox = [0.0, 0.0, 0.0, 0.0]
                    
                regions.append({
                    "id": idx + 1,
                    "text": str(text),
                    "confidence": round(score, 4),
                    "polygon": poly_coords,
                    "bbox": bbox
                })
                
        # Format B: Traditional PaddleOCR list format [[[poly], (text, score)], ...]
        elif isinstance(raw_output, list):
            items = raw_output[0] if (len(raw_output) > 0 and isinstance(raw_output[0], list)) else raw_output
            if items:
                for idx, line in enumerate(items):
                    if isinstance(line, (list, tuple)) and len(line) >= 2:
                        poly, text_info = line[0], line[1]
                        if isinstance(text_info, (list, tuple)):
                            text, score = text_info[0], float(text_info[1])
                        else:
                            text, score = str(text_info), 1.0
                            
                        poly_coords = [list(pt) for pt in poly] if isinstance(poly, (list, tuple)) else []
                        if poly_coords:
                            xs = [pt[0] for pt in poly_coords]
                            ys = [pt[1] for pt in poly_coords]
                            bbox = [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))]
                        else:
                            bbox = [0.0, 0.0, 0.0, 0.0]
                            
                        regions.append({
                            "id": idx + 1,
                            "text": str(text),
                            "confidence": round(score, 4),
                            "polygon": poly_coords,
                            "bbox": bbox
                        })
                        
        return regions

    def process_image(self, image: np.ndarray) -> List[Dict[str, Any]]:
        try:
            res = self.ocr.ocr(image)
        except Exception:
            res = self.ocr.predict(image)
            
        return self._parse_paddle_output(res)
