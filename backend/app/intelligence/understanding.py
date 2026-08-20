import re
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional, Union

from app.core.schemas import OCRDocumentResult, PageResult, RegionResult
from app.schemas.intelligence_schema import (
    DocumentIntelligenceResult, ExtractedEntity, ExtractedTable,
    DocumentElement, SourceProvenance, EntityRelationship
)

logger = logging.getLogger("DocumentUnderstandingEngine")

class DocumentUnderstandingEngine:
    """
    Generic Document Intelligence & Information Extraction System Engine.
    Consumes raw OCR result (text + bounding boxes + confidence + pages)
    and dynamically produces document classification, entity structures,
    normalized values, tables, and relationships without hard-coded universal schemas.
    """

    def __init__(self):
        self._init_ppstructure()

    def _init_ppstructure(self):
        """Initializes PPStructureV3 adapter if available in current environment."""
        self.ppstructure_engine = None
        try:
            import importlib
            paddleocr_mod = importlib.import_module("paddleocr")
            self.ppstructure_class = getattr(paddleocr_mod, "PPStructureV3", None)
            logger.info("PPStructureV3 adapter ready for document layout parsing.")
        except Exception:
            logger.info("PPStructureV3 not directly available; using geometry layout parser.")
            self.ppstructure_class = None

    def analyze_document(self, ocr_result: OCRDocumentResult) -> DocumentIntelligenceResult:
        """
        Main entry point: Analyzes OCR document result and builds generic structured intelligence.
        """
        doc_id = str(uuid.uuid4())
        filename = ocr_result.document.filename
        
        all_regions: List[Tuple[int, RegionResult]] = []
        for page in ocr_result.pages:
            for r in page.regions:
                all_regions.append((page.page_number, r))

        # 1. Infer Document Type dynamically
        document_type, doc_type_conf = self._infer_document_type(ocr_result.aggregated_text, all_regions)

        # 2. Dynamic Key-Value & Entity Extraction
        entities = self._extract_dynamic_entities(ocr_result.pages)

        # 3. Table Structure Extraction
        tables = self._extract_tables(ocr_result.pages)

        # 4. Extract High-Level Document Elements
        elements = self._extract_document_elements(ocr_result.pages)

        # 5. Entity Relationships
        relationships = self._build_relationships(entities, document_type)

        # 6. Assemble Full Structured JSON
        structured_json = {
            "document_id": doc_id,
            "filename": filename,
            "document_type": document_type,
            "confidence_score": doc_type_conf,
            "summary": {
                "total_pages": ocr_result.document.page_count,
                "total_regions": ocr_result.total_regions,
                "average_confidence": ocr_result.average_confidence,
                "entity_count": len(entities),
                "table_count": len(tables),
            },
            "fields": {e.key: {
                "label": e.label,
                "raw_value": e.raw_value,
                "normalized_value": e.normalized_value,
                "value_type": e.value_type,
                "confidence": e.confidence,
                "currency": e.currency,
                "needs_review": e.needs_review
            } for e in entities},
            "tables": [t.dict() for t in tables],
            "extracted_text": ocr_result.aggregated_text
        }

        return DocumentIntelligenceResult(
            document_id=doc_id,
            filename=filename,
            document_type=document_type,
            confidence_score=doc_type_conf,
            entities=entities,
            tables=tables,
            relationships=relationships,
            elements=elements,
            structured_json=structured_json
        )

    def _infer_document_type(self, full_text: str, all_regions: List[Tuple[int, RegionResult]]) -> Tuple[str, float]:
        """
        Dynamically infers document classification category based on semantic text patterns.
        Gracefully falls back to 'unknown' without crashing or failing.
        """
        text_lower = full_text.lower()

        keywords_map = {
            "invoice": ["invoice", "tax invoice", "bill to", "invoice no", "invoice date", "due date", "subtotal", "gstin", "vat no"],
            "receipt": ["receipt", "pos receipt", "cashier", "total paid", "change due", "subtotal", "tax invoice/receipt"],
            "flight_ticket": ["boarding pass", "pnr", "e-ticket", "airline", "flight no", "departure", "seat", "gate", "passenger"],
            "hotel_invoice": ["hotel", "check-in", "check-out", "room no", "reservation", "guest name", "tariff"],
            "bank_statement": ["account statement", "bank statement", "account number", "opening balance", "closing balance", "withdrawals", "deposits"],
            "medical_report": ["medical report", "patient name", "lab report", "diagnosis", "doctor", "hospital", "test name", "prescription"],
            "contract": ["agreement", "by and between", "terms and conditions", "whereas", "witnesseth", "signatures", "clause"],
            "form": ["application form", "applicant name", "date of birth", "declaration", "form no", "signature of applicant"],
            "certificate": ["certificate of", "certifies that", "hereby certified", "award", "registration certificate"],
        }

        scores: Dict[str, int] = {category: 0 for category in keywords_map}

        for category, kw_list in keywords_map.items():
            for kw in kw_list:
                if kw in text_lower:
                    scores[category] += 1

        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]

        if best_score >= 2:
            confidence = min(0.6 + (best_score * 0.1), 0.98)
            return best_category, round(confidence, 2)
        elif best_score == 1:
            return best_category, 0.60
        else:
            # Fallback category for unseen / custom document types
            return "unknown", 0.50

    def _extract_dynamic_entities(self, pages: List[PageResult]) -> List[ExtractedEntity]:
        """
        Extracts key-value fields and semantic entities dynamically from OCR regions.
        Handles normalization for dates, numbers, currencies, emails, phones, and identifiers.
        """
        entities: List[ExtractedEntity] = []
        seen_keys = set()

        for page in pages:
            regions = page.regions
            n_regions = len(regions)

            # Strategy 1: Explicit Inline Key-Value Patterns ("Key: Value" or "Key - Value")
            for r in regions:
                text = r.text.strip()
                if ":" in text or " -" in text or " –" in text:
                    parts = re.split(r"[:\-\u2013]", text, maxsplit=1)
                    if len(parts) == 2:
                        raw_k, raw_v = parts[0].strip(), parts[1].strip()
                        if 2 <= len(raw_k) <= 35 and len(raw_v) > 0 and not raw_k.isdigit():
                            key_slug = self._slugify_key(raw_k)
                            if key_slug not in seen_keys:
                                val_type, norm_val, curr = self._normalize_value(raw_v)
                                seen_keys.add(key_slug)
                                entities.append(ExtractedEntity(
                                    key=key_slug,
                                    label=raw_k,
                                    raw_value=raw_v,
                                    normalized_value=norm_val,
                                    value_type=val_type,
                                    confidence=round(r.confidence, 2),
                                    currency=curr,
                                    source=SourceProvenance(page=page.page_number, bbox=r.bbox, text=text),
                                    needs_review=r.confidence < 0.80
                                ))

            # Strategy 2: Spatial Layout Key-Value Association (Key region left of / above Value region)
            for i in range(n_regions):
                r1 = regions[i]
                t1 = r1.text.strip()
                
                # Check if r1 looks like a key candidate (e.g., "Total Amount", "Date", "GSTIN", "PNR")
                if len(t1) <= 35 and not t1.endswith(".") and not t1.isdigit():
                    key_slug = self._slugify_key(t1)
                    if key_slug in seen_keys or len(key_slug) < 3:
                        continue

                    # Search adjacent regions for value
                    best_match_val = None
                    best_match_region = None

                    for j in range(n_regions):
                        if i == j:
                            continue
                        r2 = regions[j]
                        t2 = r2.text.strip()

                        if not t2 or t2 == t1:
                            continue

                        # Check right-adjacent on same horizontal line
                        y_diff = abs(r1.bbox[1] - r2.bbox[1])
                        x_diff = r2.bbox[0] - r1.bbox[2]

                        if y_diff < 15 and 0 <= x_diff < 200:
                            best_match_val = t2
                            best_match_region = r2
                            break

                    if best_match_val and best_match_region:
                        val_type, norm_val, curr = self._normalize_value(best_match_val)
                        seen_keys.add(key_slug)
                        entities.append(ExtractedEntity(
                            key=key_slug,
                            label=t1,
                            raw_value=best_match_val,
                            normalized_value=norm_val,
                            value_type=val_type,
                            confidence=round(min(r1.confidence, best_match_region.confidence), 2),
                            currency=curr,
                            source=SourceProvenance(
                                page=page.page_number,
                                bbox=best_match_region.bbox,
                                text=f"{t1}: {best_match_val}"
                            ),
                            needs_review=min(r1.confidence, best_match_region.confidence) < 0.80
                        ))

            # Strategy 3: Semantic Pattern Recognizer (Dates, Currencies, Tax IDs, Emails, Phones)
            for r in regions:
                text = r.text.strip()
                
                # GST / Tax ID
                gst_match = re.search(r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b", text)
                if gst_match and "gstin" not in seen_keys:
                    seen_keys.add("gstin")
                    entities.append(ExtractedEntity(
                        key="gstin",
                        label="GSTIN / Tax ID",
                        raw_value=gst_match.group(0),
                        normalized_value=gst_match.group(0),
                        value_type="identifier",
                        confidence=round(r.confidence, 2),
                        source=SourceProvenance(page=page.page_number, bbox=r.bbox, text=text)
                    ))

                # PNR Code
                pnr_match = re.search(r"\bPNR[:\s]*([A-Z0-9]{6})\b", text, re.IGNORECASE)
                if pnr_match and "pnr_number" not in seen_keys:
                    seen_keys.add("pnr_number")
                    entities.append(ExtractedEntity(
                        key="pnr_number",
                        label="PNR Number",
                        raw_value=pnr_match.group(1),
                        normalized_value=pnr_match.group(1),
                        value_type="identifier",
                        confidence=round(r.confidence, 2),
                        source=SourceProvenance(page=page.page_number, bbox=r.bbox, text=text)
                    ))

                # Email
                email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
                if email_match and "email_address" not in seen_keys:
                    seen_keys.add("email_address")
                    entities.append(ExtractedEntity(
                        key="email_address",
                        label="Email Address",
                        raw_value=email_match.group(0),
                        normalized_value=email_match.group(0),
                        value_type="email",
                        confidence=round(r.confidence, 2),
                        source=SourceProvenance(page=page.page_number, bbox=r.bbox, text=text)
                    ))

                # Phone Number
                phone_match = re.search(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", text)
                if phone_match and "phone_number" not in seen_keys and len(phone_match.group(0)) >= 10:
                    seen_keys.add("phone_number")
                    entities.append(ExtractedEntity(
                        key="phone_number",
                        label="Phone Number",
                        raw_value=phone_match.group(0),
                        normalized_value=re.sub(r"[^\d+]", "", phone_match.group(0)),
                        value_type="phone",
                        confidence=round(r.confidence, 2),
                        source=SourceProvenance(page=page.page_number, bbox=r.bbox, text=text)
                    ))

        return entities

    def _extract_tables(self, pages: List[PageResult]) -> List[ExtractedTable]:
        """
        Extracts structured tables from pages.
        Uses visual row-column line geometry grouping.
        """
        extracted_tables: List[ExtractedTable] = []
        table_counter = 1

        for page in pages:
            regions = page.regions
            if len(regions) < 4:
                continue

            # Group regions by vertical Y alignment (rows)
            sorted_regions = sorted(regions, key=lambda r: (r.bbox[1], r.bbox[0]))
            rows_grid: List[List[RegionResult]] = []
            
            curr_row: List[RegionResult] = []
            last_y = -1

            for r in sorted_regions:
                if last_y == -1 or abs(r.bbox[1] - last_y) < 12:
                    curr_row.append(r)
                else:
                    if len(curr_row) >= 2:
                        rows_grid.append(sorted(curr_row, key=lambda item: item.bbox[0]))
                    curr_row = [r]
                last_y = r.bbox[1]

            if curr_row and len(curr_row) >= 2:
                rows_grid.append(sorted(curr_row, key=lambda item: item.bbox[0]))

            # If we detected 3+ consecutive multi-column rows, construct table object
            if len(rows_grid) >= 3:
                header_row = [r.text for r in rows_grid[0]]
                data_rows = []
                for row in rows_grid[1:]:
                    data_rows.append([r.text for r in row])

                table_bbox = [
                    min(r.bbox[0] for row in rows_grid for r in row),
                    min(r.bbox[1] for row in rows_grid for r in row),
                    max(r.bbox[2] for row in rows_grid for r in row),
                    max(r.bbox[3] for row in rows_grid for r in row),
                ]

                extracted_tables.append(ExtractedTable(
                    table_id=table_counter,
                    page_number=page.page_number,
                    headers=header_row,
                    rows=data_rows,
                    bbox=table_bbox,
                    confidence=0.92
                ))
                table_counter += 1

        return extracted_tables

    def _extract_document_elements(self, pages: List[PageResult]) -> List[DocumentElement]:
        """Categorizes document text regions into structured elements."""
        elements: List[DocumentElement] = []
        elem_id = 1

        for page in pages:
            for r in page.regions:
                text = r.text.strip()
                if not text:
                    continue

                elem_type = "text"
                if len(text) < 40 and (text.isupper() or ":" in text):
                    elem_type = "header" if ":" not in text else "key_value"

                elements.append(DocumentElement(
                    id=elem_id,
                    type=elem_type,
                    text=text,
                    bbox=r.bbox,
                    confidence=round(r.confidence, 2),
                    page_number=page.page_number
                ))
                elem_id += 1

        return elements

    def _build_relationships(self, entities: List[ExtractedEntity], doc_type: str) -> List[EntityRelationship]:
        """Builds semantic relationships between extracted entities."""
        relationships: List[EntityRelationship] = []

        entity_map = {e.key: e.raw_value for e in entities}

        if doc_type in ["invoice", "receipt"]:
            if "merchant_name" in entity_map or "total_amount" in entity_map:
                relationships.append(EntityRelationship(
                    subject=entity_map.get("merchant_name", "Vendor"),
                    predicate="issued_invoice_for",
                    object=entity_map.get("total_amount", entity_map.get("total", "Unknown Amount"))
                ))
        elif doc_type == "flight_ticket":
            if "passenger_name" in entity_map and "pnr_number" in entity_map:
                relationships.append(EntityRelationship(
                    subject=entity_map.get("passenger_name", "Passenger"),
                    predicate="holds_pnr",
                    object=entity_map.get("pnr_number", "")
                ))

        return relationships

    def _normalize_value(self, raw_str: str) -> Tuple[str, Optional[Union[str, float, int]], Optional[str]]:
        """
        Normalizes raw string values into typed representations.
        Returns: (value_type, normalized_val, currency_symbol_if_any)
        """
        clean_str = raw_str.strip()

        # 1. Currency & Amount normalization (e.g., ₹5,600.00, $120.50, EUR 45)
        curr_symbol = None
        if "₹" in clean_str or "rs" in clean_str.lower() or "inr" in clean_str.lower():
            curr_symbol = "INR"
        elif "$" in clean_str or "usd" in clean_str.lower():
            curr_symbol = "USD"
        elif "€" in clean_str or "eur" in clean_str.lower():
            curr_symbol = "EUR"
        elif "£" in clean_str or "gbp" in clean_str.lower():
            curr_symbol = "GBP"

        # Check numeric amount
        num_str = re.sub(r"[^\d.]", "", clean_str)
        if num_str and (curr_symbol or re.search(r"\b\d+\.\d{2}\b", clean_str)):
            try:
                val = float(num_str)
                return ("currency" if curr_symbol else "number"), val, curr_symbol
            except ValueError:
                pass

        # Pure Integer / Float
        if re.match(r"^-?\d+$", clean_str):
            return "number", int(clean_str), None
        if re.match(r"^-?\d+\.\d+$", clean_str):
            return "number", float(clean_str), None

        # 2. Date Normalization (Formats: YYYY-MM-DD, DD/MM/YYYY, DD-MMM-YYYY)
        date_patterns = [
            (r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b", "%Y-%m-%d"),
            (r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b", "%d/%m/%Y"),
            (r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{2})\b", "%d/%m/%y"),
        ]
        for pat, fmt in date_patterns:
            m = re.search(pat, clean_str)
            if m:
                try:
                    dt_str = m.group(0).replace(".", "/").replace("-", "/")
                    if fmt == "%Y-%m-%d":
                        dt = datetime.strptime(m.group(0).replace("/", "-"), "%Y-%m-%d")
                    elif fmt == "%d/%m/%y":
                        dt = datetime.strptime(dt_str, "%d/%m/%y")
                    else:
                        dt = datetime.strptime(dt_str, "%d/%m/%Y")
                    return "date", dt.strftime("%Y-%m-%d"), None
                except ValueError:
                    pass

        # 3. Fallback String
        return "string", clean_str, curr_symbol

    def _slugify_key(self, text: str) -> str:
        """Converts raw label string into normalized snake_case key."""
        slug = text.lower().strip()
        slug = re.sub(r"[^\w\s]", "", slug)
        slug = re.sub(r"\s+", "_", slug)
        return slug[:40]
