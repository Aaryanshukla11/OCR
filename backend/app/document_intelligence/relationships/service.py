from typing import List
from app.document_intelligence.schemas.document import (
    TextGroup, KeyValueLink, LayoutRegion, RelationshipGraph
)
from app.document_intelligence.relationships.key_value import KeyValueAssociationEngine
from app.document_intelligence.relationships.graph import RelationshipGraphBuilder

class RelationshipService:
    @staticmethod
    def process_relationships(
        groups: List[TextGroup], 
        table_regions: List[LayoutRegion], 
        page_w: float, 
        page_h: float
    ) -> List[KeyValueLink]:
        return KeyValueAssociationEngine.associate_key_value_pairs(groups, table_regions, page_w, page_h)

    @staticmethod
    def build_graph(
        regions: List[LayoutRegion], 
        groups: List[TextGroup], 
        links: List[KeyValueLink]
    ) -> RelationshipGraph:
        return RelationshipGraphBuilder.build_graph(regions, groups, links)
