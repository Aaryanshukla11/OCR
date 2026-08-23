from typing import List, Dict, Any, Tuple
from app.document_intelligence.schemas.document import ElementRef, LayoutRegion

class LayoutDetector:
    """
    Determines layout regions (HEADER, BODY, FOOTER, TABLE) and
    calculates deterministic multi-column aware reading order.
    """
    @staticmethod
    def classify_region_type(bbox: List[float], page_w: float, page_h: float, text: str = "") -> str:
        if page_h <= 0 or not bbox:
            return "body"

        ymin, ymax = bbox[1], bbox[3]
        center_y = (ymin + ymax) / 2.0
        rel_y = center_y / page_h

        # Top 15% is header candidate
        if rel_y < 0.15:
            return "header"
        # Bottom 12% is footer candidate
        elif rel_y > 0.88:
            return "footer"
            
        return "body"

    @staticmethod
    def detect_columns(elements: List[ElementRef], page_width: float) -> List[Tuple[float, float]]:
        """
        Identifies column splits in multi-column documents.
        Returns a list of column (xmin, xmax) ranges.
        """
        if not elements or page_width <= 0:
            return [(0.0, page_width)]

        # Check if elements form 2 distinct horizontal clusters
        midpoint = page_width / 2.0
        left_elements = [e for e in elements if e.bbox[2] <= midpoint + (page_width * 0.05)]
        right_elements = [e for e in elements if e.bbox[0] >= midpoint - (page_width * 0.05)]

        # If both left and right columns have elements that overlap vertically, treat as multi-column
        if len(left_elements) >= 1 and len(right_elements) >= 1:
            left_ymax = max(e.bbox[3] for e in left_elements)
            right_ymin = min(e.bbox[1] for e in right_elements)
            # Significant vertical overlap indicates side-by-side columns
            if right_ymin < left_ymax:
                return [(0.0, midpoint), (midpoint, page_width)]

        return [(0.0, page_width)]

    @staticmethod
    def sort_reading_order(elements: List[ElementRef], page_width: float, page_height: float) -> List[ElementRef]:
        """
        Sorts elements in reading order:
        First by region (Header -> Body/Tables -> Footer),
        Then by column index (Column 1 -> Column 2),
        Then top-to-bottom (ymin), then left-to-right (xmin).
        """
        if not elements:
            return []

        columns = LayoutDetector.detect_columns(elements, page_width)

        def element_key(e: ElementRef):
            region_type = LayoutDetector.classify_region_type(e.bbox, page_width, page_height, e.text)
            
            # Region priority: Header = 0, Body/Table = 1, Footer = 2
            region_prio = 0 if region_type == "header" else (2 if region_type == "footer" else 1)

            # Column index
            col_idx = 0
            for idx, (c_min, c_max) in enumerate(columns):
                center_x = (e.bbox[0] + e.bbox[2]) / 2.0
                if c_min <= center_x <= c_max:
                    col_idx = idx
                    break

            # Quantize vertical position to 12px lines to handle minor baseline jitter
            line_bucket = round(e.bbox[1] / 12.0) * 12.0
            
            return (region_prio, col_idx, line_bucket, e.bbox[0])

        return sorted(elements, key=element_key)
