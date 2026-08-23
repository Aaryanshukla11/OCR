import pytest
import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.document_intelligence.schemas.document import ElementRef, LayoutRegion, SpatialRelation, ValueCategory
from app.document_intelligence.layout.detector import LayoutDetector
from app.document_intelligence.grouping.grouper import TextGroupingEngine
from app.document_intelligence.relationships.key_value import KeyValueAssociationEngine
from app.document_intelligence.tables.detector import TableDetector
from app.document_intelligence.orchestrator import DocumentIntelligenceOrchestrator
from app.core.schemas import OCRDocumentResult, DocumentInfo, PageResult, RegionResult, ProcessingMetadata, AccuracyMetrics

def make_element(elem_id: str, text: str, bbox: list, page: int = 1) -> ElementRef:
    return ElementRef(
        id=elem_id,
        text=text,
        bbox=[float(x) for x in bbox],
        confidence=0.95,
        page=page
    )

def test_1_same_line_key_value():
    e1 = make_element("r1", "GSTIN:", [50, 100, 120, 125])
    e2 = make_element("r2", "07ABCDE1234F1Z5", [130, 100, 300, 125])
    groups = TextGroupingEngine.group_same_line_elements([e1, e2], 800, 1000)
    links = KeyValueAssociationEngine.associate_key_value_pairs(groups, [], 800, 1000)
    
    assert len(links) >= 1
    assert "GSTIN" in links[0].key_text
    assert "07ABCDE1234F1Z5" in links[0].value_text

def test_2_two_line_key_value():
    e1 = make_element("r1", "GSTIN", [50, 100, 120, 125])
    e2 = make_element("r2", "07ABCDE1234F1Z5", [50, 135, 250, 160])
    
    g1 = TextGroupingEngine.group_same_line_elements([e1], 800, 1000)[0]
    g2 = TextGroupingEngine.group_same_line_elements([e2], 800, 1000)[0]
    
    links = KeyValueAssociationEngine.associate_key_value_pairs([g1, g2], [], 800, 1000)
    assert len(links) >= 1
    assert "GSTIN" in links[0].key_text
    assert "07ABCDE1234F1Z5" in links[0].value_text
    assert links[0].spatial_relation == SpatialRelation.DIRECTLY_BELOW

def test_3_multi_word_key():
    e1 = make_element("r1", "Invoice Number:", [50, 100, 200, 125])
    e2 = make_element("r2", "INV-1024", [210, 100, 300, 125])
    
    groups = TextGroupingEngine.group_same_line_elements([e1, e2], 800, 1000)
    links = KeyValueAssociationEngine.associate_key_value_pairs(groups, [], 800, 1000)
    
    assert len(links) >= 1
    assert "Invoice Number" in links[0].key_text
    assert "INV-1024" in links[0].value_text

def test_4_table_protection():
    e1 = make_element("r1", "Item | Qty | Rate", [50, 300, 400, 325])
    e2 = make_element("r2", "Laptop | 1 | 50000", [50, 335, 400, 360])
    
    table_regions = TableDetector.detect_table_regions([e1, e2], 800, 1000)
    assert len(table_regions) >= 1
    
    groups = TextGroupingEngine.group_same_line_elements([e1, e2], 800, 1000)
    links = KeyValueAssociationEngine.associate_key_value_pairs(groups, table_regions, 800, 1000)
    
    # Table items must NOT be converted to standalone key-value pairs
    assert len(links) == 0

def test_5_multi_column_reading_order():
    col1_a = make_element("c1_a", "Column 1 Item A", [50, 200, 250, 220])
    col1_b = make_element("c1_b", "Column 1 Item B", [50, 250, 250, 270])
    
    col2_x = make_element("c2_x", "Column 2 Item X", [450, 205, 650, 225])
    col2_y = make_element("c2_y", "Column 2 Item Y", [450, 255, 650, 275])
    
    sorted_elems = LayoutDetector.sort_reading_order([col1_a, col2_x, col1_b, col2_y], 800, 1000)
    ordered_texts = [e.text for e in sorted_elems]
    
    assert ordered_texts == ["Column 1 Item A", "Column 1 Item B", "Column 2 Item X", "Column 2 Item Y"]

def test_6_header_body_footer_isolation():
    header_e = make_element("h1", "Company Header Info", [50, 20, 300, 45])
    footer_e = make_element("f1", "Page 1 of 1", [50, 920, 200, 945])
    
    header_type = LayoutDetector.classify_region_type(header_e.bbox, 800, 1000)
    footer_type = LayoutDetector.classify_region_type(footer_e.bbox, 800, 1000)
    
    assert header_type == "header"
    assert footer_type == "footer"

def test_7_handwritten_imperfect_ocr():
    e1 = make_element("r1", "GSTlN:", [50, 100, 120, 125])
    e2 = make_element("r2", "07ABCDE1234F1Z5", [130, 100, 300, 125])
    
    groups = TextGroupingEngine.group_same_line_elements([e1, e2], 800, 1000)
    links = KeyValueAssociationEngine.associate_key_value_pairs(groups, [], 800, 1000)
    
    assert len(links) >= 1
    assert "GSTlN" in links[0].key_text

def test_8_multiple_kv_pairs_one_region():
    e1 = make_element("r1", "Date: 20/08/2026", [50, 100, 250, 125])
    e2 = make_element("r2", "Invoice No: INV-99", [300, 100, 500, 125])
    
    groups = TextGroupingEngine.group_same_line_elements([e1, e2], 800, 1000)
    links = KeyValueAssociationEngine.associate_key_value_pairs(groups, [], 800, 1000)
    
    assert len(links) == 2

def test_9_key_with_value_on_right():
    e1 = make_element("r1", "Total Amount:", [50, 500, 180, 525])
    e2 = make_element("r2", "₹600.00", [190, 500, 300, 525])
    
    groups = TextGroupingEngine.group_same_line_elements([e1, e2], 800, 1000)
    links = KeyValueAssociationEngine.associate_key_value_pairs(groups, [], 800, 1000)
    
    assert len(links) >= 1
    assert links[0].value_category == ValueCategory.CURRENCY

def test_10_key_with_value_below():
    e1 = make_element("r1", "Delivery Address:", [50, 400, 200, 425])
    e2 = make_element("r2", "123 Main Street", [50, 435, 250, 460])
    
    g1 = TextGroupingEngine.group_same_line_elements([e1], 800, 1000)[0]
    g2 = TextGroupingEngine.group_same_line_elements([e2], 800, 1000)[0]
    
    links = KeyValueAssociationEngine.associate_key_value_pairs([g1, g2], [], 800, 1000)
    assert len(links) >= 1
    assert links[0].spatial_relation == SpatialRelation.DIRECTLY_BELOW

def test_11_empty_missing_value():
    e1 = make_element("r1", "Reference:", [50, 100, 150, 125])
    
    groups = TextGroupingEngine.group_same_line_elements([e1], 800, 1000)
    links = KeyValueAssociationEngine.associate_key_value_pairs(groups, [], 800, 1000)
    
    # Missing value candidate should gracefully produce 0 links without crashing
    assert len(links) == 0

def test_12_unknown_document():
    ocr_res = OCRDocumentResult(
        document=DocumentInfo(filename="unknown_doc.png", page_count=1, file_type="PNG"),
        pages=[PageResult(
            page_number=1,
            width=800,
            height=1000,
            regions=[
                RegionResult(id=1, text="Custom Doc Pass", polygon=[[10,10],[100,10],[100,30],[10,30]], bbox=[10,10,100,30], confidence=0.9),
                RegionResult(id=2, text="ID: 99120", polygon=[[10,40],[100,40],[100,60],[10,60]], bbox=[10,40,100,60], confidence=0.9)
            ],
            full_text="Custom Doc Pass\nID: 99120",
            average_confidence=90.0
        )],
        processing=ProcessingMetadata(processing_time_ms=10.0, processing_time_sec=0.01, device="CPU", model="Test", provider="Test"),
        aggregated_text="Custom Doc Pass\nID: 99120",
        average_confidence=90.0,
        total_regions=2,
        accuracy=AccuracyMetrics(available=False, message="Test"),
        status="success"
    )
    
    inter_doc = DocumentIntelligenceOrchestrator.process_document(ocr_res)
    assert inter_doc.total_pages == 1
    assert len(inter_doc.pages[0].elements) == 2
    assert inter_doc.grouping_confidence > 0

def test_13_table_detector_bbox_edge_cases():
    # Valid table bbox case
    e1 = make_element("r1", "Item | Qty | Rate", [50, 100, 400, 125])
    e2 = make_element("r2", "Widget A | 2 | 100", [50, 130, 400, 155])
    regs = TableDetector.detect_table_regions([e1, e2], 800, 1000)
    assert len(regs) == 1
    assert regs[0].bbox == [50.0, 100.0, 400.0, 155.0]

    # Missing / empty bbox case
    e_missing = ElementRef(id="m1", text="Item | Rate", bbox=[], confidence=0.9, page=1)
    regs_missing = TableDetector.detect_table_regions([e_missing], 800, 1000)
    assert len(regs_missing) == 0

    # Malformed bbox case
    e_malformed = ElementRef(id="m2", text="Item | Rate", bbox=[50.0, 100.0], confidence=0.9, page=1)
    regs_malformed = TableDetector.detect_table_regions([e_malformed], 800, 1000)
    assert len(regs_malformed) == 0

    # Safety check on is_inside_table
    assert not TableDetector.is_inside_table(None, regs)
    assert not TableDetector.is_inside_table([50, 100, 400, 155], None)

def test_14_confidence_score_normalization():
    e1 = make_element("r1", "Total:", [50, 100, 100, 120])
    e1.confidence = 0.95
    assert 0.0 <= e1.confidence <= 1.0
