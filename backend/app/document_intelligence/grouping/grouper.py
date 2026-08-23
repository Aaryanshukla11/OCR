import math
from typing import List, Dict, Any, Tuple, Optional
from app.document_intelligence.schemas.document import ElementRef, TextGroup, SpatialRelation

class TextGroupingEngine:
    """
    Spatial relationship calculation and text grouping engine.
    Calculates spatial relationships (SAME_LINE, DIRECTLY_BELOW, LEFT_OF, RIGHT_OF, NEAR, FAR)
    using relative, normalized coordinates based on box dimensions & page height/width.
    """
    @staticmethod
    def compute_spatial_relation(
        box1: List[float], 
        box2: List[float], 
        page_w: float = 800.0, 
        page_h: float = 1000.0
    ) -> SpatialRelation:
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2

        h1 = max(1.0, y1_max - y1_min)
        h2 = max(1.0, y2_max - y2_min)
        avg_h = (h1 + h2) / 2.0

        w1 = max(1.0, x1_max - x1_min)
        w2 = max(1.0, x2_max - x2_min)

        # Vertical overlap
        y_top = max(y1_min, y2_min)
        y_bot = min(y1_max, y2_max)
        v_overlap = max(0.0, y_bot - y_top)

        # Horizontal overlap
        x_left = max(x1_min, x2_min)
        x_right = min(x1_max, x2_max)
        h_overlap = max(0.0, x_right - x_left)

        center1_y = (y1_min + y1_max) / 2.0
        center2_y = (y2_min + y2_max) / 2.0

        # Check SAME_LINE: vertical overlap > 50% of avg height OR center difference < 0.4 * avg_h
        if v_overlap > (0.45 * avg_h) or abs(center1_y - center2_y) < (0.4 * avg_h):
            if x1_max <= x2_min + (0.05 * w1):
                return SpatialRelation.RIGHT_OF
            elif x2_max <= x1_min + (0.05 * w2):
                return SpatialRelation.LEFT_OF
            else:
                return SpatialRelation.SAME_LINE

        # Check DIRECTLY_BELOW / DIRECTLY_ABOVE
        if h_overlap > (0.25 * min(w1, w2)):
            if y1_max <= y2_min + (0.5 * avg_h) and (y2_min - y1_max) <= (2.5 * avg_h):
                return SpatialRelation.DIRECTLY_BELOW
            elif y2_max <= y1_min + (0.5 * avg_h) and (y1_min - y2_max) <= (2.5 * avg_h):
                return SpatialRelation.DIRECTLY_ABOVE

        # Proximity distance check (normalized by page diagonal)
        dist_x = max(0.0, x2_min - x1_max) if x2_min > x1_max else max(0.0, x1_min - x2_max)
        dist_y = max(0.0, y2_min - y1_max) if y2_min > y1_max else max(0.0, y1_min - y2_max)
        norm_dist = math.sqrt(dist_x**2 + dist_y**2) / max(1.0, math.sqrt(page_w**2 + page_h**2))

        if norm_dist < 0.12:
            return SpatialRelation.NEAR

        return SpatialRelation.FAR

    @staticmethod
    def group_same_line_elements(elements: List[ElementRef], page_w: float, page_h: float) -> List[TextGroup]:
        """
        Groups OCR fragments into logical line groups.
        Example: "Invoice" + "No:" + "INV-1024" -> "Invoice No: INV-1024"
        """
        if not elements:
            return []

        # Sort elements by line bucket first, then xmin
        def sort_key(e: ElementRef):
            center_y = (e.bbox[1] + e.bbox[3]) / 2.0
            line_bucket = round(center_y / 14.0) * 14.0
            return (line_bucket, e.bbox[0])

        sorted_elems = sorted(elements, key=sort_key)
        groups: List[TextGroup] = []
        visited = set()

        group_id_counter = 1
        for i, elem in enumerate(sorted_elems):
            if elem.id in visited:
                continue

            current_cluster = [elem]
            visited.add(elem.id)

            for j in range(i + 1, len(sorted_elems)):
                candidate = sorted_elems[j]
                if candidate.id in visited:
                    continue

                # Check if candidate is SAME_LINE or RIGHT_OF current cluster tail
                last_elem = current_cluster[-1]
                relation = TextGroupingEngine.compute_spatial_relation(last_elem.bbox, candidate.bbox, page_w, page_h)

                if relation in (SpatialRelation.SAME_LINE, SpatialRelation.RIGHT_OF):
                    # Gap check: horizontal gap between last_elem xmax and candidate xmin
                    h_gap = candidate.bbox[0] - last_elem.bbox[2]
                    h1 = last_elem.bbox[3] - last_elem.bbox[1]

                    # If last_elem or cluster already contains a complete key-val (with delimiter) and candidate has another key (with delimiter), do not merge
                    cluster_text = " ".join([e.text for e in current_cluster])
                    has_delim1 = ":" in cluster_text or "=" in cluster_text
                    has_delim2 = ":" in candidate.text or "=" in candidate.text

                    if has_delim1 and has_delim2 and h_gap > 25.0:
                        break

                    if h_gap <= max(100.0, 3.0 * h1):
                        current_cluster.append(candidate)
                        visited.add(candidate.id)

            # Build TextGroup object
            elem_ids = [e.id for e in current_cluster]
            merged_text = " ".join([e.text for e in current_cluster])
            
            xs = [e.bbox[0] for e in current_cluster] + [e.bbox[2] for e in current_cluster]
            ys = [e.bbox[1] for e in current_cluster] + [e.bbox[3] for e in current_cluster]
            bbox = [min(xs), min(ys), max(xs), max(ys)]
            
            avg_conf = float(sum(e.confidence for e in current_cluster) / len(current_cluster))

            groups.append(TextGroup(
                id=f"group_{group_id_counter}",
                element_ids=elem_ids,
                text=merged_text,
                bbox=bbox,
                confidence=round(avg_conf, 4),
                line_count=1,
                region_id=current_cluster[0].region_type
            ))
            group_id_counter += 1

        return groups
