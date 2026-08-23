import re
from typing import List, Dict, Any, Optional, Tuple
from app.document_intelligence.schemas.document import (
    TextGroup, ElementRef, KeyValueLink, ValueCategory, SpatialRelation, LayoutRegion
)
from app.document_intelligence.grouping.grouper import TextGroupingEngine
from app.document_intelligence.tables.detector import TableDetector

class KeyValueAssociationEngine:
    """
    Domain-agnostic Key-Value relationship candidate extraction engine.
    Establishes spatial & structural relationships between key candidates and value candidates.
    Supports imperfect/handwritten OCR fragments, multi-word keys, and multi-line pairs.
    """

    @staticmethod
    def classify_value_category(text: str) -> ValueCategory:
        text_clean = text.strip()
        
        # Currency: ₹, $, €, INR, USD or amount formats
        if re.search(r'[\$₹€£]|inr|usd|eur', text_clean, re.I) or re.search(r'^\d+[\.,]\d{2}$', text_clean):
            return ValueCategory.CURRENCY

        # Date: 20/08/2026, 2026-08-20, 20 Aug 2026
        if re.search(r'\b\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}\b', text_clean) or re.search(r'\b\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', text_clean, re.I):
            return ValueCategory.DATE

        # Percentage: 18%, 5.5%
        if "%" in text_clean or re.search(r'\b\d+(\.\d+)?\s*percent\b', text_clean, re.I):
            return ValueCategory.PERCENTAGE

        # Email
        if "@" in text_clean and "." in text_clean:
            return ValueCategory.EMAIL

        # Phone
        if re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text_clean):
            return ValueCategory.PHONE

        # Identifier: INV-1024, 07ABCDE1234F1Z5, PNR-991
        if re.search(r'^[A-Z0-9]{3,}[-/#]?[A-Z0-9]{2,}$', text_clean) and any(c.isdigit() for c in text_clean):
            return ValueCategory.IDENTIFIER

        # Number: 500, 1024
        if re.match(r'^\d+(\.\d+)?$', text_clean):
            return ValueCategory.NUMBER

        return ValueCategory.TEXT

    @staticmethod
    def is_key_candidate(text: str) -> Tuple[bool, float, Optional[str], Optional[str]]:
        """
        Determines if text is a likely key candidate.
        Returns: (is_key, confidence, key_prefix, inline_value)
        Supports colon, equals, label-like short text, and imperfect OCR fragments.
        """
        raw = text.strip()
        if not raw or len(raw) > 50:
            return False, 0.0, None, None

        # Inline delimiter split: "GSTIN: 07ABCDE1234F1Z5" -> key="GSTIN", val="07ABCDE1234F1Z5"
        for delim in [":", "=", " - "]:
            if delim in raw:
                parts = raw.split(delim, 1)
                k_part = parts[0].strip()
                v_part = parts[1].strip() if len(parts) > 1 else ""
                if 1 <= len(k_part.split()) <= 6:
                    return True, 0.95, k_part, (v_part if v_part else None)

        # If text is predominantly a specific value type (Identifier, Currency, Date, Number) or starts with digits without delimiter, it is NOT a key
        if re.match(r'^\d', raw) and not (":" in raw or "=" in raw):
            return False, 0.0, None, None

        val_cat = KeyValueAssociationEngine.classify_value_category(raw)
        if val_cat in (ValueCategory.IDENTIFIER, ValueCategory.CURRENCY, ValueCategory.DATE, ValueCategory.NUMBER, ValueCategory.PERCENTAGE, ValueCategory.EMAIL, ValueCategory.PHONE):
            return False, 0.0, None, None

        # Label-like indicators or imperfect OCR patterns (e.g. GSTlN, Invoice No., Date, Bill To, Amt, Total)
        words = raw.split()
        if 1 <= len(words) <= 4:
            # Common key suffix or label format
            if raw.endswith(":") or raw.endswith(".") or raw.endswith("="):
                return True, 0.90, raw.rstrip(":.-="), None

            # Short text label candidate (e.g. "Customer Name", "GSTlN", "Invoice No", "Bill To", "Delivery Address")
            if not re.match(r'^\d+$', raw) and not "@" in raw:
                is_label_like = all(w[0].isupper() for w in words if w) or raw.isupper()
                conf = 0.85 if is_label_like else 0.70
                return True, conf, raw, None

        return False, 0.0, None, None

    @staticmethod
    def associate_key_value_pairs(
        groups: List[TextGroup], 
        table_regions: Optional[List[LayoutRegion]] = None, 
        page_w: float = 800.0, 
        page_h: float = 1000.0
    ) -> List[KeyValueLink]:
        if not groups:
            return []

        links: List[KeyValueLink] = []
        table_regs = table_regions or []
        used_values = set()

        for i, group in enumerate(groups):
            # Table protection: Skip key-value extraction for groups inside table regions
            if TableDetector.is_inside_table(group.bbox, table_regs):
                continue

            is_key, key_conf, key_label, inline_val = KeyValueAssociationEngine.is_key_candidate(group.text)
            if not is_key or not key_label:
                continue

            # Case A: Inline value present in same group ("GSTIN: 07ABCDE1234F1Z5")
            if inline_val:
                val_cat = KeyValueAssociationEngine.classify_value_category(inline_val)
                links.append(KeyValueLink(
                    key_text=key_label,
                    value_text=inline_val,
                    key_region=group.id,
                    value_region=group.id,
                    relationship="KEY_VALUE",
                    confidence=key_conf,
                    value_category=val_cat,
                    key_bbox=group.bbox,
                    value_bbox=group.bbox,
                    spatial_relation=SpatialRelation.SAME_LINE
                ))
                continue

            # Case B: Search spatial neighbors for target value (Same-line on Right OR Line directly Below)
            best_target: Optional[TextGroup] = None
            best_relation: SpatialRelation = SpatialRelation.FAR
            best_score = -1.0

            for j, candidate in enumerate(groups):
                if j == i or candidate.id in used_values:
                    continue
                if TableDetector.is_inside_table(candidate.bbox, table_regs):
                    continue

                relation = TextGroupingEngine.compute_spatial_relation(group.bbox, candidate.bbox, page_w, page_h)

                # Target must be on RIGHT_OF (same line) OR DIRECTLY_BELOW
                if relation in (SpatialRelation.RIGHT_OF, SpatialRelation.SAME_LINE, SpatialRelation.DIRECTLY_BELOW):
                    # Region check: Don't link across different layout regions (e.g. Header to Footer)
                    if group.region_id and candidate.region_id and group.region_id != candidate.region_id:
                        continue

                    # Don't pick another obvious key as value
                    cand_is_key, _, _, cand_inline = KeyValueAssociationEngine.is_key_candidate(candidate.text)
                    if cand_is_key and not cand_inline:
                        continue

                    val_cat = KeyValueAssociationEngine.classify_value_category(candidate.text)
                    
                    # Score pairing: RIGHT_OF preferred over DIRECTLY_BELOW
                    base_score = 0.95 if relation in (SpatialRelation.RIGHT_OF, SpatialRelation.SAME_LINE) else 0.85
                    if val_cat != ValueCategory.TEXT:
                        base_score += 0.05

                    if base_score > best_score:
                        best_score = base_score
                        best_target = candidate
                        best_relation = relation

            if best_target:
                used_values.add(best_target.id)
                val_cat = KeyValueAssociationEngine.classify_value_category(best_target.text)
                links.append(KeyValueLink(
                    key_text=key_label,
                    value_text=best_target.text,
                    key_region=group.id,
                    value_region=best_target.id,
                    relationship="KEY_VALUE",
                    confidence=round(key_conf * best_score, 4),
                    value_category=val_cat,
                    key_bbox=group.bbox,
                    value_bbox=best_target.bbox,
                    spatial_relation=best_relation
                ))

        return links
