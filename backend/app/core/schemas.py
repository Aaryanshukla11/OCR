from pydantic import BaseModel
from typing import List, Optional, Any

class DocumentInfo(BaseModel):
    filename: str
    page_count: int
    file_type: str

class RegionResult(BaseModel):
    id: int
    text: str
    polygon: List[List[float]]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    bbox: List[float]            # [xmin, ymin, xmax, ymax]
    confidence: float

class PageResult(BaseModel):
    page_number: int
    width: int
    height: int
    regions: List[RegionResult]
    full_text: str
    average_confidence: float

class ProcessingMetadata(BaseModel):
    processing_time_ms: float
    processing_time_sec: float
    device: str
    model: str
    provider: str

class AccuracyMetrics(BaseModel):
    available: bool
    ground_truth: Optional[str] = None
    cer: Optional[float] = None
    wer: Optional[float] = None
    message: str

class OCRDocumentResult(BaseModel):
    document: DocumentInfo
    pages: List[PageResult]
    processing: ProcessingMetadata
    aggregated_text: str
    average_confidence: float
    total_regions: int
    accuracy: AccuracyMetrics
    status: str = "success"
