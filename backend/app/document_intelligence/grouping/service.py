from typing import List
from app.document_intelligence.schemas.document import ElementRef, TextGroup
from app.document_intelligence.grouping.grouper import TextGroupingEngine

class GroupingService:
    @staticmethod
    def group_elements(elements: List[ElementRef], page_w: float, page_h: float) -> List[TextGroup]:
        return TextGroupingEngine.group_same_line_elements(elements, page_w, page_h)
