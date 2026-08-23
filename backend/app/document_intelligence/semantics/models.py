from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SemanticCandidate(BaseModel):
    canonical_name: str
    display_label: str
    confidence: float = 0.0
    evidence: List[str] = Field(default_factory=list)
    candidate_type: str = "rule_candidate"

class SemanticContext(BaseModel):
    field_text: str
    value_text: str
    nearby_text: List[str] = Field(default_factory=list)
    parent_region: Optional[str] = None
    region_type: str = "body"
    page_number: int = 1
    document_type: str = "unknown"
    table_context: Optional[Dict[str, Any]] = None
    column_name: Optional[str] = None
    row_context: List[str] = Field(default_factory=list)
    neighboring_fields: List[str] = Field(default_factory=list)
    neighboring_values: List[str] = Field(default_factory=list)
    ocr_confidence: float = 1.0
    grouping_confidence: float = 1.0
    relationship_confidence: float = 1.0
    value_type: str = "UNKNOWN"
    bbox: Optional[List[float]] = None

class SemanticFieldResult(BaseModel):
    source_field: str
    value: str
    identified_as: str
    display_label: str
    qwen_prediction: Optional[str] = None
    final_prediction: Optional[str] = None
    semantic_source: str = "ollama"
    ocr_confidence: float = 1.0
    grouping_confidence: float = 1.0
    relationship_confidence: float = 1.0
    semantic_confidence: float = 1.0
    final_confidence: float = 1.0
    evidence: List[str] = Field(default_factory=list)
    evidence_details: Dict[str, Any] = Field(default_factory=dict)
    needs_review: bool = False
    candidates: List[SemanticCandidate] = Field(default_factory=list)
    bbox: Optional[List[float]] = None

class SemanticColumnResult(BaseModel):
    original_header: str
    identified_as: str
    display_label: str
    confidence: float = 1.0
    evidence: List[str] = Field(default_factory=list)

class SemanticDocumentResult(BaseModel):
    fields: List[SemanticFieldResult] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    overall_confidence: float = 1.0
