from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SpatialRelation(str, Enum):
    SAME_LINE = "SAME_LINE"
    DIRECTLY_BELOW = "DIRECTLY_BELOW"
    DIRECTLY_ABOVE = "DIRECTLY_ABOVE"
    LEFT_OF = "LEFT_OF"
    RIGHT_OF = "RIGHT_OF"
    INSIDE_REGION = "INSIDE_REGION"
    SAME_REGION = "SAME_REGION"
    NEAR = "NEAR"
    FAR = "FAR"
    TABLE_CELL = "TABLE_CELL"
    SEPARATED = "SEPARATED"

class ValueCategory(str, Enum):
    DATE = "date"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    IDENTIFIER = "identifier"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    NUMBER = "number"
    TEXT = "text"
    CODE = "code"

class ElementRef(BaseModel):
    id: str
    text: str
    bbox: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])  # [xmin, ymin, xmax, ymax]
    polygon: Optional[List[List[float]]] = None
    confidence: float = 1.0
    page: int = 1
    region_type: str = "body"
    reading_order: int = 0

class LayoutRegion(BaseModel):
    id: str
    type: str  # "header", "body", "footer", "table", "sidebar"
    bbox: List[float]
    reading_order: int
    element_ids: List[str] = Field(default_factory=list)

class TextGroup(BaseModel):
    id: str
    element_ids: List[str]
    text: str
    bbox: List[float]
    confidence: float
    line_count: int = 1
    region_id: Optional[str] = None

class KeyValueLink(BaseModel):
    key_text: str
    value_text: str
    key_region: str
    value_region: str
    relationship: str = "KEY_VALUE"
    confidence: float = 0.90
    value_category: ValueCategory = ValueCategory.TEXT
    key_bbox: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    value_bbox: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    spatial_relation: SpatialRelation = SpatialRelation.RIGHT_OF

class RelationshipGraphNode(BaseModel):
    id: str
    label: str
    type: str  # "KEY", "VALUE", "GROUP", "REGION"
    bbox: List[float]

class RelationshipGraphEdge(BaseModel):
    source: str
    target: str
    type: str  # "KEY_VALUE", "CONTAINS", "TABLE_CELL", "NEXT_LINE"
    confidence: float

class RelationshipGraph(BaseModel):
    nodes: List[RelationshipGraphNode] = Field(default_factory=list)
    edges: List[RelationshipGraphEdge] = Field(default_factory=list)

class IntermediatePage(BaseModel):
    page: int
    width: float
    height: float
    regions: List[LayoutRegion] = Field(default_factory=list)
    elements: List[ElementRef] = Field(default_factory=list)
    groups: List[TextGroup] = Field(default_factory=list)
    relationships: List[KeyValueLink] = Field(default_factory=list)
    reading_order: List[str] = Field(default_factory=list)  # Ordered element/group IDs

class IntermediateDocument(BaseModel):
    filename: str
    total_pages: int
    pages: List[IntermediatePage] = Field(default_factory=list)
    ocr_confidence: float = 0.0
    grouping_confidence: float = 0.0
    relationship_confidence: float = 0.0
    graph: RelationshipGraph = Field(default_factory=RelationshipGraph)
    semantic_results: Optional[Dict[str, Any]] = None
