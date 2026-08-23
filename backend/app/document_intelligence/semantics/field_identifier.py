from typing import List, Dict, Any, Optional
from app.document_intelligence.schemas.document import IntermediateDocument, IntermediatePage
from app.document_intelligence.semantics.models import (
    SemanticDocumentResult, SemanticFieldResult, SemanticColumnResult
)
from app.document_intelligence.semantics.context_builder import ContextBuilder
from app.document_intelligence.semantics.semantic_classifier import SemanticClassifier
from app.document_intelligence.semantics.ontology import CANONICAL_ONTOLOGY

class FieldIdentifier:
    """
    Main Semantic Identification Engine.
    Converts IntermediateDocument key-value links, text groups, and table columns
    into canonical semantic identities without hardcoded business schemas.
    """

    def __init__(self):
        self.classifier = SemanticClassifier()

    def process_document(self, inter_doc: IntermediateDocument) -> SemanticDocumentResult:
        if not inter_doc or not inter_doc.pages:
            return SemanticDocumentResult(fields=[], tables=[], overall_confidence=1.0)

        semantic_fields: List[SemanticFieldResult] = []
        semantic_tables: List[Dict[str, Any]] = []
        processed_pairs = set()

        all_contexts: List[Dict[str, Any]] = []

        for page in inter_doc.pages:
            # 1. Process explicit Key-Value Links
            for link in page.relationships:
                pair_key = (link.key_text.strip(), link.value_text.strip())
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)

                ctx = ContextBuilder.build_context_for_link(link, page, inter_doc)
                all_contexts.append({
                    "context": ctx,
                    "type": "kv_link",
                    "bbox": link.value_bbox
                })

            # 2. Process unlinked key candidate text groups if not already paired
            for g in page.groups:
                g_text = g.text.strip()
                if not g_text or any(c["context"].field_text == g_text or c["context"].value_text == g_text for c in all_contexts):
                    continue

                ctx = ContextBuilder.build_context_for_group(g, page, inter_doc)
                all_contexts.append({
                    "context": ctx,
                    "type": "group",
                    "bbox": g.bbox
                })

        # Run batch classification across all accumulated field contexts
        batch_results = self.classifier.classify_batch([item["context"] for item in all_contexts])

        for item, field_res in zip(all_contexts, batch_results):
            field_res.bbox = item["bbox"]
            if item["type"] == "kv_link" or field_res.identified_as != "unknown_field" or field_res.semantic_confidence >= 0.70:
                semantic_fields.append(field_res)

        # 3. Process Table Column Semantics
        for page in inter_doc.pages:
            for reg in page.regions:
                if reg.type == "table" and reg.element_ids:
                    col_results: List[SemanticColumnResult] = []
                    table_elems = [e for e in page.elements if e.id in reg.element_ids]
                    col_contexts = []
                    headers = table_elems[:6]
                    for elem in headers:
                        ctx = ContextBuilder.build_context_for_table_column(
                            column_header=elem.text,
                            sample_values=[e.text for e in table_elems if e.id != elem.id][:3],
                            page=page,
                            inter_doc=inter_doc
                        )
                        col_contexts.append((elem.text, ctx))

                    c_results = self.classifier.classify_batch([c[1] for c in col_contexts])
                    for (orig_hdr, _), c_res in zip(col_contexts, c_results):
                        col_results.append(SemanticColumnResult(
                            original_header=orig_hdr,
                            identified_as=c_res.identified_as,
                            display_label=c_res.display_label,
                            confidence=c_res.final_confidence,
                            evidence=c_res.evidence
                        ))
                    semantic_tables.append({
                        "region_id": reg.id,
                        "columns": [c.model_dump() for c in col_results]
                    })

        overall_conf = 1.0
        if semantic_fields:
            overall_conf = round(sum(f.final_confidence for f in semantic_fields) / len(semantic_fields), 4)

        return SemanticDocumentResult(
            fields=semantic_fields,
            tables=semantic_tables,
            overall_confidence=overall_conf
        )
