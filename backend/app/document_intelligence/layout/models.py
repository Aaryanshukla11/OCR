from pydantic import BaseModel
from typing import List, Optional

class ColumnBoundary(BaseModel):
    column_id: int
    xmin: float
    xmax: float

class LayoutAnalysisResult(BaseModel):
    page_number: int
    columns: List[ColumnBoundary]
    regions: List[dict]
    reading_order_ids: List[str]
