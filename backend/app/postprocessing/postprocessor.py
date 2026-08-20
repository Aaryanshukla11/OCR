import re
from typing import List, Dict, Any
import numpy as np
from app.core.config import PostprocessingConfig

class Postprocessor:
    """
    Standardized postprocessing layer for text normalization,
    reading order sorting, and confidence score calculation.
    """
    def __init__(self, config: PostprocessingConfig):
        self.config = config

    def _normalize_text(self, text: str) -> str:
        if not self.config.normalize_whitespace:
            return text
        # Collapse excessive horizontal spaces but preserve line breaks
        lines = text.splitlines()
        normalized_lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in lines]
        return "\n".join(normalized_lines)

    def process_page_regions(self, raw_regions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not raw_regions:
            return []

        processed = []
        for reg in raw_regions:
            item = dict(reg)
            item["text"] = self._normalize_text(item.get("text", ""))
            processed.append(item)

        # Optional reading order sorting (top-to-bottom by ymin, then left-to-right by xmin)
        if self.config.sort_reading_order:
            processed.sort(key=lambda r: (round(r["bbox"][1] / 15) * 15, r["bbox"][0]))
            
            # Re-index ids sequentially after sorting
            for i, r in enumerate(processed):
                r["id"] = i + 1

        return processed

    def calculate_confidence(self, regions: List[Dict[str, Any]]) -> float:
        if not regions:
            return 0.0
        scores = [r.get("confidence", 0.0) for r in regions]
        avg = float(np.mean(scores))
        return round(avg * 100, 1) if avg <= 1.0 else round(avg, 1)
