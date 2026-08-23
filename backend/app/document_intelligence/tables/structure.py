from pydantic import BaseModel
from typing import List, Any

class TableStructureResult(BaseModel):
    table_id: str
    page_number: int
    headers: List[str]
    rows: List[List[str]]
    bbox: List[float]
    confidence: float
