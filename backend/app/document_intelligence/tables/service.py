from typing import List
from app.document_intelligence.schemas.document import ElementRef, LayoutRegion
from app.document_intelligence.tables.detector import TableDetector

class TableService:
    @staticmethod
    def get_table_regions(elements: List[ElementRef], page_w: float, page_h: float) -> List[LayoutRegion]:
        return TableDetector.detect_table_regions(elements, page_w, page_h)
