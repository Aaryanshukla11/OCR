from typing import List, Tuple
from app.document_intelligence.schemas.document import ElementRef, LayoutRegion
from app.document_intelligence.layout.detector import LayoutDetector

class LayoutService:
    @staticmethod
    def process_layout(elements: List[ElementRef], page_w: float, page_h: float) -> Tuple[List[LayoutRegion], List[ElementRef]]:
        sorted_elements = LayoutDetector.sort_reading_order(elements, page_w, page_h)
        
        # Update reading_order indices
        for idx, elem in enumerate(sorted_elements):
            elem.reading_order = idx + 1

        # Group elements into LayoutRegions
        region_map = {"header": [], "body": [], "footer": [], "table": []}
        for elem in sorted_elements:
            rtype = LayoutDetector.classify_region_type(elem.bbox, page_w, page_h, elem.text)
            elem.region_type = rtype
            if rtype not in region_map:
                region_map[rtype] = []
            region_map[rtype].append(elem)

        layout_regions = []
        reg_id_counter = 1
        for rtype, r_elems in region_map.items():
            if not r_elems:
                continue
            xs = [e.bbox[0] for e in r_elems] + [e.bbox[2] for e in r_elems]
            ys = [e.bbox[1] for e in r_elems] + [e.bbox[3] for e in r_elems]
            bbox = [min(xs), min(ys), max(xs), max(ys)]
            
            layout_regions.append(LayoutRegion(
                id=f"region_{reg_id_counter}_{rtype}",
                type=rtype,
                bbox=bbox,
                reading_order=reg_id_counter,
                element_ids=[e.id for e in r_elems]
            ))
            reg_id_counter += 1

        return layout_regions, sorted_elements
