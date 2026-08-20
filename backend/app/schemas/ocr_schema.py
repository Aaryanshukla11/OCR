from pydantic import BaseModel
from typing import List, Optional, Any

class BoundingBoxRegion(BaseModel):
    id: int
    text: str
    confidence: float
    polygon: List[List[float]]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    bbox: List[float]            # [xmin, ymin, xmax, ymax]

class PageOCRResult(BaseModel):
    page_number: int
    regions: List[BoundingBoxRegion]
    extracted_text: str
    average_confidence: float

class AccuracyMetrics(BaseModel):
    available: bool
    ground_truth: Optional[str] = None
    cer: Optional[float] = None
    wer: Optional[float] = None
    message: str

class OCRResponse(BaseModel):
    filename: str
    file_type: str
    total_pages: int
    processing_time: float
    device: str
    average_confidence: float
    total_regions: int
    pages: List[PageOCRResult]
    aggregated_text: str
    accuracy: AccuracyMetrics
    status: str = "success"

class HistoryItem(BaseModel):
    id: str
    filename: str
    timestamp: str
    processing_time: float
    total_regions: int
    average_confidence: float
    device: str
    status: str
    file_type: str
    pages_count: int
