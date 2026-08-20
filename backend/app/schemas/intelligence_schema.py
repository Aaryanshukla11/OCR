from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class SourceProvenance(BaseModel):
    page: int = 1
    bbox: List[float] = Field(default_factory=list) # [xmin, ymin, xmax, ymax]
    text: str = ""

class ExtractedEntity(BaseModel):
    key: str
    label: str
    raw_value: str
    normalized_value: Optional[Union[str, float, int, bool]] = None
    value_type: str = "string"  # string | number | currency | date | datetime | percentage | identifier | person | organization | location | email | phone | address | boolean | unknown
    confidence: float = 1.0
    source: Optional[SourceProvenance] = None
    needs_review: bool = False
    currency: Optional[str] = None

class ExtractedTable(BaseModel):
    table_id: int
    page_number: int = 1
    headers: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    bbox: List[float] = Field(default_factory=list)
    confidence: float = 1.0

class DocumentElement(BaseModel):
    id: int
    type: str  # text | header | key_value | table | list
    text: str
    bbox: List[float] = Field(default_factory=list)
    confidence: float = 1.0
    page_number: int = 1

class EntityRelationship(BaseModel):
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0

class DocumentIntelligenceResult(BaseModel):
    document_id: str
    filename: str
    document_type: str  # invoice | receipt | flight_ticket | bank_statement | medical_report | contract | form | certificate | unknown
    confidence_score: float = 1.0
    entities: List[ExtractedEntity] = Field(default_factory=list)
    tables: List[ExtractedTable] = Field(default_factory=list)
    relationships: List[EntityRelationship] = Field(default_factory=list)
    elements: List[DocumentElement] = Field(default_factory=list)
    structured_json: Dict[str, Any] = Field(default_factory=dict)

class StoredDocumentSummary(BaseModel):
    id: str
    filename: str
    document_type: str
    created_at: str
    total_pages: int
    average_confidence: float
    entity_count: int
    table_count: int
    needs_review_count: int
    key_highlights: Dict[str, Any] = Field(default_factory=dict)

class QueryPlan(BaseModel):
    query_text: str
    target_document_type: Optional[str] = None
    field_key: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    search_terms: List[str] = Field(default_factory=list)
    aggregation: str = "NONE"  # NONE | SUM | COUNT | AVG | MIN | MAX
    sql_executed: str = ""

class QueryResponse(BaseModel):
    query: str
    plan: QueryPlan
    answer_summary: str
    total_matches: int
    aggregated_value: Optional[Union[float, int, str]] = None
    documents: List[StoredDocumentSummary] = Field(default_factory=list)
    matching_entities: List[ExtractedEntity] = Field(default_factory=list)
