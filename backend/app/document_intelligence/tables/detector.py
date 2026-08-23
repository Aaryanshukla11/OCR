import re
from typing import List, Dict, Any, Optional
from app.document_intelligence.schemas.document import ElementRef, LayoutRegion

class TableDetector:
    """
    Table Protection & Table Region Detection.
    Ensures that table grid cells (Item | Qty | Rate | Total) are protected
    from being misclassified as key-value pairs.
    """
    TABLE_HEADER_KEYWORDS = [
        "item", "description", "qty", "quantity", "rate", "price", "unit price",
        "amount", "total", "subtotal", "tax", "gst", "cgst", "sgst", "discount"
    ]

    @staticmethod
    def is_table_header_line(text: str) -> bool:
        lower = text.lower()
        # Look for multi-column patterns or multiple keywords in a single line
        matched = [kw for kw in TableDetector.TABLE_HEADER_KEYWORDS if re.search(r'\b' + re.escape(kw) + r'\b', lower)]
        return len(matched) >= 2 or "|" in text or "\t" in text

    @staticmethod
    def detect_table_regions(elements: List[ElementRef], page_w: float, page_h: float) -> List[LayoutRegion]:
        """
        Detects table regions based on header rows and consecutive aligned data rows.
        """
        if not elements:
            return []

        table_regions: List[LayoutRegion] = []
        table_elem_ids: List[str] = []
        in_table = False
        table_bbox: Optional[List[float]] = None

        for elem in elements:
            if not elem.bbox or len(elem.bbox) < 4:
                continue

            if TableDetector.is_table_header_line(elem.text):
                in_table = True
                if table_bbox is None:
                    table_bbox = list(elem.bbox)
                else:
                    table_bbox[0] = min(table_bbox[0], elem.bbox[0])
                    table_bbox[1] = min(table_bbox[1], elem.bbox[1])
                    table_bbox[2] = max(table_bbox[2], elem.bbox[2])
                    table_bbox[3] = max(table_bbox[3], elem.bbox[3])
                table_elem_ids.append(elem.id)
            elif in_table:
                # Check if numbers/prices or table row structure continues
                if re.search(r'\d+', elem.text) or "|" in elem.text:
                    table_elem_ids.append(elem.id)
                    if table_bbox is None:
                        table_bbox = list(elem.bbox)
                    else:
                        table_bbox[0] = min(table_bbox[0], elem.bbox[0])
                        table_bbox[1] = min(table_bbox[1], elem.bbox[1])
                        table_bbox[2] = max(table_bbox[2], elem.bbox[2])
                        table_bbox[3] = max(table_bbox[3], elem.bbox[3])
                else:
                    in_table = False

        if table_elem_ids and table_bbox:
            table_regions.append(LayoutRegion(
                id="table_region_1",
                type="table",
                bbox=table_bbox,
                reading_order=1,
                element_ids=table_elem_ids
            ))

        return table_regions

    @staticmethod
    def is_inside_table(bbox: Optional[List[float]], table_regions: Optional[List[LayoutRegion]]) -> bool:
        """
        Checks if a bounding box falls within any identified table region.
        """
        if not bbox or len(bbox) < 4 or not table_regions:
            return False

        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0

        for t_reg in table_regions:
            if not t_reg or not t_reg.bbox or len(t_reg.bbox) < 4:
                continue
            tb = t_reg.bbox
            if tb[0] <= cx <= tb[2] and tb[1] <= cy <= tb[3]:
                return True

        return False
