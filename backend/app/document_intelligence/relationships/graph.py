from typing import List
from app.document_intelligence.schemas.document import (
    TextGroup, KeyValueLink, LayoutRegion, RelationshipGraph,
    RelationshipGraphNode, RelationshipGraphEdge
)

class RelationshipGraphBuilder:
    """
    Constructs an intermediate directed relationship graph representation of document entities.
    Nodes represent Regions, Groups, Keys, Values.
    Edges represent KEY_VALUE, CONTAINS, and TABLE_CELL relationships.
    """
    @staticmethod
    def build_graph(
        regions: List[LayoutRegion],
        groups: List[TextGroup],
        kv_links: List[KeyValueLink]
    ) -> RelationshipGraph:
        nodes: List[RelationshipGraphNode] = []
        edges: List[RelationshipGraphEdge] = []
        node_ids = set()

        # Add Layout Region Nodes
        for r in regions:
            n_id = f"region_node_{r.id}"
            if n_id not in node_ids:
                nodes.append(RelationshipGraphNode(
                    id=n_id,
                    label=f"Region: {r.type.upper()}",
                    type="REGION",
                    bbox=r.bbox
                ))
                node_ids.add(n_id)

        # Add Text Group Nodes & CONTAINS edges from Region -> Group
        for g in groups:
            g_node_id = f"group_node_{g.id}"
            if g_node_id not in node_ids:
                nodes.append(RelationshipGraphNode(
                    id=g_node_id,
                    label=g.text[:30],
                    type="GROUP",
                    bbox=g.bbox
                ))
                node_ids.add(g_node_id)

            if g.region_id:
                r_node_id = f"region_node_{g.region_id}"
                if r_node_id in node_ids:
                    edges.append(RelationshipGraphEdge(
                        source=r_node_id,
                        target=g_node_id,
                        type="CONTAINS",
                        confidence=1.0
                    ))

        # Add Key-Value Nodes & Edges
        for link in kv_links:
            key_node_id = f"kv_key_{link.key_region}"
            val_node_id = f"kv_val_{link.value_region}"

            if key_node_id not in node_ids:
                nodes.append(RelationshipGraphNode(
                    id=key_node_id,
                    label=f"KEY: {link.key_text}",
                    type="KEY",
                    bbox=link.key_bbox
                ))
                node_ids.add(key_node_id)

            if val_node_id not in node_ids:
                nodes.append(RelationshipGraphNode(
                    id=val_node_id,
                    label=f"VALUE: {link.value_text}",
                    type="VALUE",
                    bbox=link.value_bbox
                ))
                node_ids.add(val_node_id)

            edges.append(RelationshipGraphEdge(
                source=key_node_id,
                target=val_node_id,
                type="KEY_VALUE",
                confidence=link.confidence
            ))

        return RelationshipGraph(nodes=nodes, edges=edges)
