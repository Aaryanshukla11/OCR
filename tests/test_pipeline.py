import io
import pytest
import numpy as np
from PIL import Image, ImageDraw
from app.core.pipeline import OCRPipeline
from app.core.schemas import OCRDocumentResult

def create_synthetic_test_image() -> bytes:
    img = Image.new('RGB', (400, 100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 30), "OCR ENGINE TEST", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def test_ocr_pipeline_execution():
    pipeline = OCRPipeline.get_instance()
    img_bytes = create_synthetic_test_image()
    
    result = pipeline.process_file(
        file_bytes=img_bytes,
        filename="test_synthetic.png",
        ground_truth="OCR ENGINE TEST"
    )
    
    assert isinstance(result, OCRDocumentResult)
    assert result.status == "success"
    assert result.document.filename == "test_synthetic.png"
    assert result.document.page_count == 1
    assert result.processing.model == "PaddleOCR 3.7.0"
    assert result.processing.provider == "PaddleOCR"
    assert len(result.pages) == 1
    assert result.accuracy.available is True
