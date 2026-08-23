import pytest
import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.document_intelligence.schemas.document import ElementRef, LayoutRegion, SpatialRelation, TextGroup, KeyValueLink, IntermediatePage, IntermediateDocument
from app.document_intelligence.semantics.service import SemanticService
from app.document_intelligence.semantics.context_builder import ContextBuilder
from app.document_intelligence.semantics.candidate_generator import CandidateGenerator
from app.document_intelligence.semantics.semantic_classifier import SemanticClassifier
from app.document_intelligence.semantics.ontology import CANONICAL_ONTOLOGY

def make_link(key: str, val: str, rel: SpatialRelation = SpatialRelation.RIGHT_OF) -> KeyValueLink:
    return KeyValueLink(
        key_text=key,
        value_text=val,
        key_region="r1",
        value_region="r2",
        confidence=0.95,
        key_bbox=[50, 100, 150, 125],
        value_bbox=[160, 100, 300, 125],
        spatial_relation=rel
    )

def make_doc(links: list, groups: list = None, regions: list = None) -> IntermediateDocument:
    page = IntermediatePage(
        page=1,
        width=800,
        height=1000,
        regions=regions or [],
        elements=[],
        groups=groups or [],
        relationships=links,
        reading_order=[]
    )
    return IntermediateDocument(
        filename="test_doc.pdf",
        total_pages=1,
        pages=[page],
        ocr_confidence=95.0,
        grouping_confidence=92.0,
        relationship_confidence=90.0
    )

def test_1_name_to_person_name():
    link = make_link("Name", "Aryan Kumar")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "person_name"
    assert res.fields[0].display_label == "Person Name"

def test_2_ph_to_contact_number():
    link = make_link("Ph.", "9810929812")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "contact_number"

def test_3_mobile_to_contact_number():
    link = make_link("Mobile", "9818680709")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "contact_number"

def test_4_gstin_to_gstin():
    link = make_link("GSTIN", "07AAACS0229G1ZR")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "gstin"

def test_5_invoice_no_to_invoice_number():
    link = make_link("Invoice No.", "INAT252610666")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "invoice_number"

def test_6_date_to_invoice_date():
    link = make_link("Date", "24/01/2026")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "invoice_date"

def test_7_travel_dt_to_travel_date():
    link = make_link("Travel Dt.", "25/01/2026")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "travel_date"

def test_8_ticket_no_to_ticket_number():
    link = make_link("Ticket No.", "015405004824")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "ticket_number"

def test_9_cgst_percent_to_cgst_rate():
    link = make_link("CGST %", "9%")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "cgst_rate"

def test_10_cgst_amount_to_cgst_amount():
    link = make_link("CGST Amount", "₹450.00")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "cgst_amount"

def test_11_sgst_percent_to_sgst_rate():
    link = make_link("SGST %", "9%")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "sgst_rate"

def test_12_sgst_amount_to_sgst_amount():
    link = make_link("SGST Amount", "₹450.00")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "sgst_amount"

def test_13_account_number_to_bank_account_number():
    link = make_link("Account Number", "9818680709")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "bank_account_number"

def test_14_ifsc_to_ifsc_code():
    link = make_link("IFSC Code", "SBIN0001234")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "ifsc_code"

def test_15_email_to_email_address():
    link = make_link("E-mail", "aryan@example.com")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "email_address"

def test_16_same_numeric_value_different_context():
    l1 = make_link("Mobile", "9818680709")
    l2 = make_link("Account Number", "9818680709")
    doc = make_doc([l1, l2])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 2
    f_map = {f.source_field: f.identified_as for f in res.fields}
    assert f_map["Mobile"] == "contact_number"
    assert f_map["Account Number"] == "bank_account_number"

def test_17_unknown_field():
    link = make_link("Xylophone Code", "XY-900")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "unknown_field"

def test_18_low_confidence_ambiguous_field():
    ctx = ContextBuilder.build_context_for_group(
        group=TextGroup(id="g1", element_ids=["e1"], text="Unknown Label 123", bbox=[0,0,10,10], confidence=0.4),
        page=IntermediatePage(page=1, width=800, height=1000, regions=[], elements=[], groups=[], relationships=[], reading_order=[])
    )
    classifier = SemanticClassifier()
    res = classifier.classify_field(ctx)
    assert res.needs_review is True

def test_19_table_column_semantic_identification():
    reg = LayoutRegion(id="tr1", type="table", bbox=[50,200,750,500], reading_order=1, element_ids=["e1", "e2"])
    e1 = ElementRef(id="e1", text="Travel Dt.", bbox=[50,200,150,220], confidence=0.9, page=1)
    e2 = ElementRef(id="e2", text="Ticket No.", bbox=[160,200,300,220], confidence=0.9, page=1)
    
    page = IntermediatePage(page=1, width=800, height=1000, regions=[reg], elements=[e1, e2], groups=[], relationships=[], reading_order=[])
    doc = IntermediateDocument(filename="table_doc.pdf", total_pages=1, pages=[page])
    
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.tables) >= 1
    cols = res.tables[0]["columns"]
    c_map = {c["original_header"]: c["identified_as"] for c in cols}
    assert c_map["Travel Dt."] == "travel_date"
    assert c_map["Ticket No."] == "ticket_number"

def test_20_missing_field_label():
    group = TextGroup(id="g1", element_ids=["e1"], text="07AAACS0229G1ZR", bbox=[50,100,200,120], confidence=0.95)
    page = IntermediatePage(page=1, width=800, height=1000, regions=[], elements=[], groups=[group], relationships=[], reading_order=[])
    doc = IntermediateDocument(filename="unlabelled.pdf", total_pages=1, pages=[page])
    
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) >= 1
    assert res.fields[0].identified_as == "gstin"

def test_21_handwritten_corrupted_ocr():
    link = make_link("GSTlN", "07AAACS0229G1ZR")
    doc = make_doc([link])
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "gstin"

def test_22_unknown_document_type():
    link = make_link("Custom Form ID", "FORM-9981")
    doc = make_doc([link])
    doc.filename = "random_form.pdf"
    res = SemanticService.get_instance().process_document(doc)
    assert len(res.fields) == 1
    assert res.overall_confidence > 0.0

def test_23_qwen_mock_and_validation_override(monkeypatch):
    class MockOllama:
        is_available = True
        def analyze_semantic_batch(self, items):
            # Mock Qwen predicting contact_number for bank account field
            return [{
                "field_id": 0,
                "identified_as": "contact_number",
                "display_label": "Contact Number",
                "confidence": 0.90
            }]

    classifier = SemanticClassifier()
    classifier.ollama_client = MockOllama()

    ctx = ContextBuilder.build_context_for_group(
        group=TextGroup(id="g1", element_ids=["e1"], text="Account Number 015405004824", bbox=[0,0,10,10], confidence=0.9),
        page=IntermediatePage(page=1, width=800, height=1000, regions=[], elements=[], groups=[], relationships=[], reading_order=[])
    )
    ctx.field_text = "Account Number"
    ctx.value_text = "015405004824"
    ctx.neighboring_fields = ["Bank Name", "IFSC Code"]

    res = classifier.classify_field(ctx)
    # Validator layer should override Qwen's contact_number prediction to bank_account_number due to bank context
    assert res.identified_as == "bank_account_number"
    assert res.needs_review is True

def test_24_batch_mode_multiple_fields(monkeypatch):
    class MockOllamaBatch:
        is_available = True
        def analyze_semantic_batch(self, items):
            return [
                {"field_id": 0, "identified_as": "invoice_number", "display_label": "Invoice Number", "confidence": 0.95},
                {"field_id": 1, "identified_as": "invoice_date", "display_label": "Invoice Date", "confidence": 0.95}
            ]

    classifier = SemanticClassifier()
    classifier.ollama_client = MockOllamaBatch()

    l1 = make_link("Inv #", "INV-100")
    l2 = make_link("Date", "2026-01-01")
    doc = make_doc([l1, l2])

    service = SemanticService()
    service.field_identifier.classifier = classifier
    res = service.process_document(doc)

    assert len(res.fields) == 2
    f_map = {f.source_field: f.identified_as for f in res.fields}
    assert f_map["Inv #"] == "invoice_number"
    assert f_map["Date"] == "invoice_date"

def test_25_malformed_json_fallback(monkeypatch):
    class MockOllamaMalformed:
        is_available = True
        def analyze_semantic_batch(self, items):
            return None  # Simulate malformed JSON failure after retries

    classifier = SemanticClassifier()
    classifier.ollama_client = MockOllamaMalformed()

    l1 = make_link("GSTIN", "07AAACS0229G1ZR")
    doc = make_doc([l1])

    service = SemanticService()
    service.field_identifier.classifier = classifier
    res = service.process_document(doc)

    assert len(res.fields) == 1
    assert res.fields[0].identified_as == "gstin"
    assert res.fields[0].semantic_source == "fallback"
