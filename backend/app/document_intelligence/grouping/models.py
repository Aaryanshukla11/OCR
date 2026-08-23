from pydantic import BaseModel
from typing import List, Optional

class SpatialRelationResult(BaseModel):
    source_id: str
    target_id: str
    relation: str
    distance_norm: float
    vertical_overlap: float
    horizontal_overlap: float
