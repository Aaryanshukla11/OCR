import pytest
import sys
import os
import shutil
import tempfile

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import importlib

schemas = importlib.import_module("app.core.schemas")
OCRDocumentResult = schemas.OCRDocumentResult
DocumentInfo = schemas.DocumentInfo
PageResult = schemas.PageResult
RegionResult = schemas.RegionResult
ProcessingMetadata = schemas.ProcessingMetadata
AccuracyMetrics = schemas.AccuracyMetrics

understanding = importlib.import_module("app.intelligence.understanding")
DocumentUnderstandingEngine = understanding.DocumentUnderstandingEngine

database = importlib.import_module("app.services.database")
DatabaseService = database.DatabaseService

query_engine = importlib.import_module("app.services.query_engine")
DocumentQueryEngine = query_engine.DocumentQueryEngine

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """Sets up a temporary SQLite database for testing."""
    test_db = str(tmp_path / "test_intelligence.db")
    DatabaseService.DB_PATH = test_db
    DatabaseService.init_db()
    yield
    if os.path.exists(test_db):
        os.remove(test_db)

def create_mock_ocr_result(filename="test_invoice.png", text_lines=None):
    if text_lines is None:
        text_lines = [
            "TAX INVOICE",
            "Merchant: ABC Retail Store",
            "GSTIN: 07ABCDE1234F1Z5",
            "Invoice No: INV-2026-99",
            "Invoice Date: 20/08/2026",
            "Item 1: Premium Coffee  Qty: 2  Price: 400.00",
            "Item 2: Sandwich        Qty: 1  Price: 150.00",
            "Subtotal: 550.00",
            "Tax: 50.00",
            "Total Amount: ₹600.00"
        ]

    regions = []
    for idx, line in enumerate(text_lines):
        regions.append(RegionResult(
            id=idx + 1,
            text=line,
            polygon=[[10, idx * 30], [300, idx * 30], [300, (idx + 1) * 30], [10, (idx + 1) * 30]],
            bbox=[10, idx * 30, 300, (idx + 1) * 30],
            confidence=0.96
        ))

    return OCRDocumentResult(
        document=DocumentInfo(filename=filename, page_count=1, file_type="PNG"),
        pages=[PageResult(
            page_number=1,
            width=800,
            height=1000,
            regions=regions,
            full_text="\n".join(text_lines),
            average_confidence=0.96
        )],
        processing=ProcessingMetadata(
            processing_time_ms=120.0,
            processing_time_sec=0.12,
            device="CPU",
            model="PaddleOCR 3.7.0",
            provider="PaddleOCRProvider"
        ),
        aggregated_text="\n".join(text_lines),
        average_confidence=96.0,
        total_regions=len(regions),
        accuracy=AccuracyMetrics(available=False, message="Unit test"),
        status="success"
    )

def test_document_understanding():
    engine = DocumentUnderstandingEngine()
    mock_ocr = create_mock_ocr_result()

    intel_result = engine.analyze_document(mock_ocr)

    assert intel_result.document_type == "invoice"
    assert intel_result.confidence_score >= 0.60
    assert len(intel_result.entities) > 0

    # Verify extracted keys
    keys = [e.key for e in intel_result.entities]
    assert any("merchant" in k for k in keys) or any("gstin" in k for k in keys)

def test_value_normalization():
    engine = DocumentUnderstandingEngine()

    val_type, norm_val, curr = engine._normalize_value("₹5,600.00")
    assert val_type == "currency"
    assert norm_val == 5600.0
    assert curr == "INR"

    val_type_dt, norm_dt, _ = engine._normalize_value("20/08/2026")
    assert val_type_dt == "date"
    assert norm_dt == "2026-08-20"

def test_sqlite_structured_storage():
    engine = DocumentUnderstandingEngine()
    mock_ocr = create_mock_ocr_result(filename="receipt_123.png")

    intel_result = engine.analyze_document(mock_ocr)
    doc_id = DatabaseService.save_document(
        intel_result=intel_result,
        total_pages=1,
        average_confidence=96.0,
        raw_text=mock_ocr.aggregated_text
    )

    assert doc_id == intel_result.document_id

    # Retrieve stored structured summaries
    docs = DatabaseService.get_documents()
    assert len(docs) == 1
    assert "INVOICE" in docs[0].title_highlight

    # Retrieve detailed payload
    detail = DatabaseService.get_document_by_id(doc_id)
    assert detail is not None
    assert detail["document_type"] == "invoice"
    assert len(detail["entities"]) > 0

def test_query_engine():
    engine = DocumentUnderstandingEngine()
    mock_ocr = create_mock_ocr_result(filename="august_bill.png")

    intel_result = engine.analyze_document(mock_ocr)
    DatabaseService.save_document(
        intel_result=intel_result,
        total_pages=1,
        average_confidence=96.0,
        raw_text=mock_ocr.aggregated_text
    )

    # Test Query Execution
    response = DocumentQueryEngine.execute_query("Show me all invoices")
    assert response.total_matches >= 1
    assert "INVOICE" in response.documents[0].title_highlight

    # Test Aggregation Query
    sum_response = DocumentQueryEngine.execute_query("How much did I spend on invoices?")
    assert sum_response.aggregated_value is not None

def test_unknown_document():
    """Verifies that an unseen/custom document type degrades gracefully without crashing."""
    engine = DocumentUnderstandingEngine()

    custom_text = [
        "Special Membership Pass",
        "Member ID: MEM-99120",
        "Holder: John Doe",
        "Issued: 15/05/2026",
        "Status: Active"
    ]

    mock_ocr = create_mock_ocr_result(filename="custom_pass.png", text_lines=custom_text)
    intel_result = engine.analyze_document(mock_ocr)

    # Unknown document should infer unknown/custom category gracefully without error
    assert intel_result.document_type in ["unknown", "certificate", "form"]
    assert len(intel_result.entities) > 0
