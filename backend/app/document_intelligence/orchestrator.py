from typing import List, Dict, Any
from app.document_intelligence.schemas.document import (
    ElementRef, LayoutRegion, TextGroup, KeyValueLink,
    RelationshipGraph, IntermediatePage, IntermediateDocument
)
from app.document_intelligence.layout.service import LayoutService
from app.document_intelligence.tables.service import TableService
from app.document_intelligence.grouping.service import GroupingService
from app.document_intelligence.relationships.service import RelationshipService

class DocumentIntelligenceOrchestrator:
    """
    Main orchestrator for Document Intelligence Intermediate Layer.
    Converts raw OCR page results into normalized IntermediateDocument containing
    layout regions, text groups, spatial relationships, key-value links, and graph.
    """

    @staticmethod
    def process_document(ocr_result_data: Any) -> IntermediateDocument:
        filename = getattr(ocr_result_data.document, "filename", "document.png") if hasattr(ocr_result_data, "document") else "document.png"
        pages_input = getattr(ocr_result_data, "pages", [])

        intermediate_pages: List[IntermediatePage] = []
        all_graph_nodes = []
        all_graph_edges = []
        all_ocr_confs = []
        all_group_confs = []
        all_rel_confs = []

        for p in pages_input:
            p_num = getattr(p, "page_number", 1)
            p_w = float(getattr(p, "width", 800))
            p_h = float(getattr(p, "height", 1000))
            raw_regions = getattr(p, "regions", [])

            # Convert raw OCR regions to ElementRef objects
            elements: List[ElementRef] = []
            for r in raw_regions:
                r_id = str(getattr(r, "id", f"r_{len(elements)+1}"))
                r_text = getattr(r, "text", "")
                r_bbox = getattr(r, "bbox", [0.0, 0.0, 0.0, 0.0])
                r_poly = getattr(r, "polygon", [])
                r_conf = float(getattr(r, "confidence", 1.0))
                
                elements.append(ElementRef(
                    id=f"p{p_num}_{r_id}",
                    text=r_text,
                    bbox=r_bbox,
                    polygon=r_poly,
                    confidence=r_conf,
                    page=p_num
                ))
                all_ocr_confs.append(r_conf)

            # 1. Layout Processing
            layout_regions, sorted_elements = LayoutService.process_layout(elements, p_w, p_h)

            # 2. Table Protection Detection
            table_regions = TableService.get_table_regions(sorted_elements, p_w, p_h)
            all_regions = layout_regions + [t for t in table_regions if t.id not in [r.id for r in layout_regions]]

            # 3. Text Grouping
            groups = GroupingService.group_elements(sorted_elements, p_w, p_h)
            for g in groups:
                all_group_confs.append(g.confidence)

            # 4. Key-Value Candidate Association
            kv_links = RelationshipService.process_relationships(groups, table_regions, p_w, p_h)
            for link in kv_links:
                all_rel_confs.append(link.confidence)

            # 5. Graph Building
            graph = RelationshipService.build_graph(all_regions, groups, kv_links)
            all_graph_nodes.extend(graph.nodes)
            all_graph_edges.extend(graph.edges)

            reading_order_ids = [e.id for e in sorted_elements]

            intermediate_pages.append(IntermediatePage(
                page=p_num,
                width=p_w,
                height=p_h,
                regions=all_regions,
                elements=sorted_elements,
                groups=groups,
                relationships=kv_links,
                reading_order=reading_order_ids
            ))

        avg_ocr_conf = (sum(all_ocr_confs) / len(all_ocr_confs)) if all_ocr_confs else 0.0
        avg_group_conf = (sum(all_group_confs) / len(all_group_confs)) if all_group_confs else 0.0
        avg_rel_conf = (sum(all_rel_confs) / len(all_rel_confs)) if all_rel_confs else 0.0

        merged_graph = RelationshipGraph(nodes=all_graph_nodes, edges=all_graph_edges)

        inter_doc = IntermediateDocument(
            filename=filename,
            total_pages=len(intermediate_pages),
            pages=intermediate_pages,
            ocr_confidence=round(avg_ocr_conf * 100, 1) if avg_ocr_conf <= 1.0 else round(avg_ocr_conf, 1),
            grouping_confidence=round(avg_group_conf * 100, 1) if avg_group_conf <= 1.0 else round(avg_group_conf, 1),
            relationship_confidence=round(avg_rel_conf * 100, 1) if avg_rel_conf <= 1.0 else round(avg_rel_conf, 1),
            graph=merged_graph
        )

        # 6. Semantic Field & Table Identification Engine
        try:
            from app.document_intelligence.semantics.service import SemanticService
            sem_res = SemanticService.get_instance().process_document(inter_doc)
            inter_doc.semantic_results = sem_res.model_dump()
        except Exception as sem_err:
            import logging
            logging.getLogger("Orchestrator").error(f"Semantic processing error: {sem_err}")

        return inter_doc
