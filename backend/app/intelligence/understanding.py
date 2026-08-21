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
        try:
            from app.intelligence.ollama_client import OllamaUnderstandingClient
            self.ollama_client = OllamaUnderstandingClient()
        except Exception as e:
            logger.warning(f"Could not initialize Ollama client: {e}")
            self.ollama_client = None

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
        3-STEP PIPELINE:
        STEP 1: PaddleOCR reads document & extracts raw text, geometry & regions.
        STEP 2: Qwen LLM via Ollama understands semantic meaning (e.g. INV-1024 -> invoice_number).
        STEP 3: OCR Engine validates Qwen data against OCR bounding boxes, normalizes format & stores in SQLite.
        """
        doc_id = str(uuid.uuid4())
        
        all_regions: List[Tuple[int, RegionResult]] = []
        region_snippets: List[str] = []
        for page in ocr_result.pages:
            for r in page.regions:
                all_regions.append((page.page_number, r))
                region_snippets.append(r.text)

        # STEP 1: PaddleOCR Data
        raw_ocr_text = ocr_result.aggregated_text

        # STEP 2: Qwen LLM via Ollama Semantic Understanding
        ollama_data = self.ollama_client.analyze_document_text(raw_ocr_text, region_snippets) if self.ollama_client else None

        extraction_method = "qwen_ollama"
        document_type = "unknown"
        doc_type_conf = 0.85
        raw_entities: List[Dict[str, Any]] = []

        if ollama_data and isinstance(ollama_data, dict):
            document_type = ollama_data.get("document_type", "unknown")
            doc_type_conf = float(ollama_data.get("confidence_score", 0.90))
            raw_entities = ollama_data.get("entities", [])
            logger.info(f"Step 2: Qwen LLM extracted {len(raw_entities)} entities for '{document_type}' via Ollama.")
        else:
            extraction_method = "heuristic_fallback"
            logger.info("Step 2: Ollama unreachable or unavailable; using OCR Engine heuristic understanding fallback.")
            document_type, doc_type_conf = self._infer_document_type(raw_ocr_text, all_regions)
            extracted_heuristic = self._extract_dynamic_entities(ocr_result.pages)
            raw_entities = [{
                "key": e.key,
                "label": e.label,
                "raw_value": e.raw_value,
                "value_type": e.value_type
            } for e in extracted_heuristic]

        # STEP 3: OCR Engine Validation, Format Normalization & Provenance Linking
        validated_entities: List[ExtractedEntity] = []
        for item in raw_entities:
            key = item.get("key", "").strip().lower().replace(" ", "_")
            label = item.get("label", key.replace("_", " ").title())
            raw_val = str(item.get("raw_value", "")).strip()

            if not key or not raw_val:
                continue

            # Validate against PaddleOCR actual text & bounding boxes
            matched_region = None
            validation_status = "UNVERIFIED"
            match_confidence = 0.80

            raw_val_lower = raw_val.lower()
            for pg_num, r in all_regions:
                r_text_lower = r.text.lower()
                if raw_val_lower in r_text_lower or r_text_lower in raw_val_lower:
                    matched_region = (pg_num, r)
                    validation_status = "VALIDATED" if raw_val_lower == r_text_lower else "OCR_MATCHED"
                    match_confidence = r.confidence
                    break

            provenance = None
            if matched_region:
                pg_num, r = matched_region
                provenance = SourceProvenance(
                    page=pg_num,
                    bbox=r.bbox,
                    text=r.text
                )

            # Normalize values
            val_type, norm_val, curr = self._normalize_value(raw_val)

            entity = ExtractedEntity(
                key=key,
                label=label,
                raw_value=raw_val,
                normalized_value=norm_val if norm_val is not None else raw_val,
                value_type=val_type,
                confidence=round(match_confidence, 2),
                source=provenance,
                needs_review=(validation_status == "UNVERIFIED" or match_confidence < 0.70),
                currency=curr,
                validation_status=validation_status,
                extraction_method=extraction_method
            )
            validated_entities.append(entity)

        # Table & Layout Extraction
        tables = self._extract_tables(ocr_result.pages)
        elements = self._extract_document_elements(ocr_result.pages)
        relationships = self._build_relationships(validated_entities, document_type)

        title_highlight, key_highlights = self._build_title_and_highlights(document_type, validated_entities)

        # Build Document-Centric Dynamic Table Dataset
        dynamic_columns = []
        header_record = {}
        for e in validated_entities:
            dynamic_columns.append({
                "column_name": e.key,
                "label": e.label,
                "type": e.value_type
            })
            header_record[e.key] = e.normalized_value if e.normalized_value is not None else e.raw_value

        table_rows = []
        for t in tables:
            headers = t.headers if t.headers else [f"col_{i+1}" for i in range(len(t.rows[0]) if t.rows else 0)]
            for r in t.rows:
                row_dict = dict(header_record)
                for h, val in zip(headers, r):
                    clean_h = str(h).strip().lower().replace(" ", "_")
                    row_dict[clean_h] = val
                    if not any(c["column_name"] == clean_h for c in dynamic_columns):
                        dynamic_columns.append({"column_name": clean_h, "label": str(h), "type": "string"})
                table_rows.append(row_dict)

        dynamic_dataset = {
            "dataset_id": f"dataset_{doc_id}",
            "document_type": document_type,
            "title": title_highlight,
            "columns": dynamic_columns,
            "header_record": header_record,
            "table_rows": table_rows if table_rows else [header_record]
        }

        # Assemble Full Structured Information JSON
        structured_json = {
            "document_id": doc_id,
            "document_type": document_type,
            "title_highlight": title_highlight,
            "confidence_score": doc_type_conf,
            "extraction_method": extraction_method,
            "key_highlights": key_highlights,
            "summary": {
                "total_pages": ocr_result.document.page_count,
                "total_regions": ocr_result.total_regions,
                "average_confidence": ocr_result.average_confidence,
                "entity_count": len(validated_entities),
                "table_count": len(tables),
            },
            "fields": {e.key: {
                "label": e.label,
                "raw_value": e.raw_value,
                "normalized_value": e.normalized_value,
                "value_type": e.value_type,
                "confidence": e.confidence,
                "currency": e.currency,
                "needs_review": e.needs_review,
                "validation_status": e.validation_status,
                "extraction_method": e.extraction_method,
                "provenance": e.source.dict() if e.source else None
            } for e in validated_entities},
            "tables": [t.dict() for t in tables],
            "relationships": [r.dict() for r in relationships],
            "dynamic_dataset": dynamic_dataset
        }

        return DocumentIntelligenceResult(
            document_id=doc_id,
            document_type=document_type,
            confidence_score=doc_type_conf,
            entities=validated_entities,
            tables=tables,
            relationships=relationships,
            elements=elements,
            structured_json=structured_json
        )

    def _build_title_and_highlights(self, document_type: str, entities: List[ExtractedEntity]) -> Tuple[str, Dict[str, Any]]:
        entity_map = {e.key: e.raw_value for e in entities}

        title_parts = [document_type.replace("_", " ").upper()]
        highlights = {}

        if document_type in ["invoice", "receipt"]:
            merchant = entity_map.get("merchant_name") or entity_map.get("vendor") or entity_map.get("merchant")
            inv_no = entity_map.get("invoice_number") or entity_map.get("receipt_number") or entity_map.get("invoice_no")
            total = entity_map.get("total_amount") or entity_map.get("total") or entity_map.get("amount_due")

            if merchant:
                title_parts.append(merchant)
                highlights["merchant"] = merchant
            if inv_no:
                highlights["invoice_number"] = inv_no
            if total:
                highlights["total"] = total

        elif document_type == "flight_ticket":
            passenger = entity_map.get("passenger_name") or entity_map.get("passenger")
            pnr = entity_map.get("pnr_number") or entity_map.get("pnr")
            route = entity_map.get("route") or entity_map.get("flight")

            if passenger:
                title_parts.append(passenger)
                highlights["passenger"] = passenger
            if pnr:
                highlights["pnr"] = pnr
            if route:
                highlights["route"] = route

        elif document_type == "hotel_invoice":
            guest = entity_map.get("guest_name") or entity_map.get("guest")
            hotel = entity_map.get("hotel_name") or entity_map.get("hotel")
            if guest:
                title_parts.append(guest)
                highlights["guest"] = guest
            if hotel:
                highlights["hotel"] = hotel

        else:
            # For unknown / custom document types, take first 2 prominent extracted entities
            prominent = []
            for e in entities[:3]:
                prominent.append(f"{e.label}: {e.raw_value}")
                highlights[e.key] = e.raw_value
            if prominent:
                title_parts.extend(prominent[:2])

        title_highlight = " • ".join(title_parts)
        return title_highlight, highlights


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
