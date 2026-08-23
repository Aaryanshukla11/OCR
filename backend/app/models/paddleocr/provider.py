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

import cv2

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
            
        page_items = raw_output if isinstance(raw_output, list) else [raw_output]
        region_id_counter = 1
        
        for page_data in page_items:
            if not page_data:
                continue
                
            # If page_data has an inner 'res' key/attribute (PaddleX 3.x result container format)
            target_data = page_data
            if hasattr(page_data, 'res') and getattr(page_data, 'res'):
                target_data = getattr(page_data, 'res')
            elif isinstance(page_data, dict) and 'res' in page_data and isinstance(page_data['res'], (dict, list)):
                target_data = page_data['res']

            # Format A: Paddlex 3.x / PaddleOCR 3.7+ dictionary or object format
            if isinstance(target_data, dict) or hasattr(target_data, 'get'):
                texts = target_data.get('rec_texts')
                if texts is None:
                    texts = target_data.get('texts')
                if texts is None:
                    texts = target_data.get('text')
                if texts is None:
                    texts = []

                scores = target_data.get('rec_scores')
                if scores is None:
                    scores = target_data.get('scores')
                if scores is None:
                    scores = []

                polys = target_data.get('rec_polys')
                if polys is None:
                    polys = target_data.get('dt_polys')
                if polys is None:
                    polys = target_data.get('polys')

                boxes = target_data.get('rec_boxes')
                if boxes is None:
                    boxes = target_data.get('boxes')
                
                if isinstance(texts, str):
                    texts = [texts]
                    
                for idx, text in enumerate(texts):
                    score = float(scores[idx]) if (scores and idx < len(scores)) else 1.0
                    
                    poly_coords = []
                    if polys is not None and idx < len(polys):
                        p = polys[idx]
                        if hasattr(p, 'tolist'):
                            poly_coords = p.tolist()
                        elif isinstance(p, (list, tuple)):
                            poly_coords = [list(pt) for pt in p]
                            
                    if not poly_coords and boxes is not None and idx < len(boxes):
                        b = boxes[idx]
                        if hasattr(b, 'tolist'):
                            b = b.tolist()
                        if len(b) >= 4:
                            poly_coords = [
                                [float(b[0]), float(b[1])],
                                [float(b[2]), float(b[1])],
                                [float(b[2]), float(b[3])],
                                [float(b[0]), float(b[3])]
                            ]
                        
                    if poly_coords:
                        xs = [pt[0] for pt in poly_coords]
                        ys = [pt[1] for pt in poly_coords]
                        bbox = [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))]
                    else:
                        bbox = [0.0, 0.0, 0.0, 0.0]
                        
                    regions.append({
                        "id": region_id_counter,
                        "text": str(text),
                        "confidence": round(score, 4),
                        "polygon": poly_coords,
                        "bbox": bbox
                    })
                    region_id_counter += 1
                    
            # Format B: Traditional PaddleOCR list format [[[poly], (text, score)], ...]
            elif isinstance(page_data, (list, tuple)):
                items = page_data[0] if (len(page_data) > 0 and isinstance(page_data[0], list) and len(page_data[0]) > 0 and isinstance(page_data[0][0], (list, tuple))) else page_data
                for line in items:
                    if not line:
                        continue
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
                            "id": region_id_counter,
                            "text": str(text),
                            "confidence": round(score, 4),
                            "polygon": poly_coords,
                            "bbox": bbox
                        })
                        region_id_counter += 1
                        
        return regions

    def process_image(self, image: np.ndarray) -> List[Dict[str, Any]]:
        if isinstance(image, np.ndarray) and image.ndim == 3 and image.shape[2] == 3:
            bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        else:
            bgr_image = image

        try:
            res = self.ocr.predict(bgr_image)
        except Exception:
            try:
                res = self.ocr.ocr(bgr_image)
            except Exception:
                res = self.ocr.ocr(image)
            
        return self._parse_paddle_output(res)
