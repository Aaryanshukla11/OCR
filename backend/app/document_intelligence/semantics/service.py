from typing import Optional
from app.document_intelligence.schemas.document import IntermediateDocument
from app.document_intelligence.semantics.models import SemanticDocumentResult
from app.document_intelligence.semantics.field_identifier import FieldIdentifier

class SemanticService:
    """
    Service facade for the Semantic Field Identification Engine.
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.field_identifier = FieldIdentifier()

    def process_document(self, inter_doc: IntermediateDocument) -> SemanticDocumentResult:
        return self.field_identifier.process_document(inter_doc)
