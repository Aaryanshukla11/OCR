from typing import List, Dict, Any, Optional
from app.document_intelligence.schemas.document import (
    IntermediateDocument, IntermediatePage, TextGroup, KeyValueLink, LayoutRegion
)
from app.document_intelligence.semantics.models import SemanticContext
from app.document_intelligence.semantics.ontology import detect_value_type

class ContextBuilder:
    """
    Constructs rich semantic context objects containing field text, value, value type,
    nearby OCR snippets, parent region type, table column/row metadata, and confidence scores.
    """

    @staticmethod
    def build_context_for_link(
        link: KeyValueLink,
        page: IntermediatePage,
        inter_doc: Optional[IntermediateDocument] = None
    ) -> SemanticContext:
        field_text = link.key_text.strip()
        value_text = link.value_text.strip()

        val_type = detect_value_type(value_text)

        # Region classification
        region_type = "body"
        parent_region = None
        if link.key_region or link.value_region:
            reg_id = link.key_region or link.value_region
            for r in page.regions:
                if r.id == reg_id or (r.element_ids and (reg_id in r.element_ids)):
                    region_type = r.type
                    parent_region = r.id
                    break

        # Nearby snippets (spatial proximity)
        nearby_snippets = []
        for g in page.groups:
            if g.text and g.text != field_text and g.text != value_text:
                if abs(g.bbox[1] - link.key_bbox[1]) < 100:
                    nearby_snippets.append(g.text)
                if len(nearby_snippets) >= 5:
                    break

        # Neighboring fields & values
        neigh_fields = [rel.key_text for rel in page.relationships if rel.key_text != field_text][:4]
        neigh_values = [rel.value_text for rel in page.relationships if rel.value_text != value_text][:4]

        doc_type = "unknown"
        if inter_doc and hasattr(inter_doc, 'document_type'):
            doc_type = getattr(inter_doc, 'document_type', 'unknown')

        return SemanticContext(
            field_text=field_text,
            value_text=value_text,
            nearby_text=nearby_snippets,
            parent_region=parent_region,
            region_type=region_type,
            page_number=page.page,
            document_type=doc_type,
            neighboring_fields=neigh_fields,
            neighboring_values=neigh_values,
            ocr_confidence=round(link.confidence, 4),
            grouping_confidence=inter_doc.grouping_confidence if inter_doc else 0.90,
            relationship_confidence=link.confidence,
            value_type=val_type.value
        )

    @staticmethod
    def build_context_for_group(
        group: TextGroup,
        page: IntermediatePage,
        inter_doc: Optional[IntermediateDocument] = None
    ) -> SemanticContext:
        field_text = group.text.strip()
        value_text = group.text.strip()
        val_type = detect_value_type(value_text)

        region_type = "body"
        for r in page.regions:
            if r.id == group.region_id:
                region_type = r.type
                break

        nearby_snippets = [g.text for g in page.groups if g.id != group.id and abs(g.bbox[1] - group.bbox[1]) < 80][:5]

        return SemanticContext(
            field_text=field_text,
            value_text=value_text,
            nearby_text=nearby_snippets,
            parent_region=group.region_id,
            region_type=region_type,
            page_number=page.page,
            document_type=getattr(inter_doc, 'document_type', 'unknown') if inter_doc else 'unknown',
            ocr_confidence=round(group.confidence, 4),
            grouping_confidence=inter_doc.grouping_confidence if inter_doc else 0.90,
            relationship_confidence=0.80,
            value_type=val_type.value
        )

    @staticmethod
    def build_context_for_table_column(
        column_header: str,
        sample_values: List[str],
        page: IntermediatePage,
        inter_doc: Optional[IntermediateDocument] = None
    ) -> SemanticContext:
        sample_val_str = sample_values[0] if sample_values else ""
        val_type = detect_value_type(sample_val_str) if sample_val_str else "UNKNOWN"

        return SemanticContext(
            field_text=column_header,
            value_text=sample_val_str,
            nearby_text=sample_values[:5],
            region_type="table",
            page_number=page.page,
            document_type=getattr(inter_doc, 'document_type', 'unknown') if inter_doc else 'unknown',
            table_context={"column_name": column_header, "sample_values": sample_values},
            column_name=column_header,
            row_context=sample_values[:3],
            value_type=val_type if isinstance(val_type, str) else val_type.value
        )
