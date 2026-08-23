import logging
from typing import List, Dict, Any, Tuple, Optional
from app.document_intelligence.semantics.models import (
    SemanticContext, SemanticCandidate, SemanticFieldResult
)
from app.document_intelligence.semantics.ontology import CANONICAL_ONTOLOGY
from app.document_intelligence.semantics.candidate_generator import CandidateGenerator

logger = logging.getLogger("SemanticClassifier")

class SemanticClassifier:
    """
    Primary LLM-based (Qwen/Ollama) semantic classifier for EVERY extracted field,
    backed by deterministic rule validation, evidence details, and graceful offline fallback.
    """

    def __init__(self):
        self.ollama_client = None
        try:
            from app.intelligence.ollama_client import OllamaUnderstandingClient
            self.ollama_client = OllamaUnderstandingClient()
        except Exception as e:
            logger.info(f"Ollama client not available for semantic classifier: {e}")
            self.ollama_client = None

    def classify_field(self, context: SemanticContext) -> SemanticFieldResult:
        """Classifies a single field context through Ollama + Validator Layer."""
        batch_results = self.classify_batch([context])
        return batch_results[0] if batch_results else self._fallback_classify(context)

    def classify_batch(self, contexts: List[SemanticContext]) -> List[SemanticFieldResult]:
        """
        Classifies a batch of field contexts using local Ollama/Qwen as the primary engine.
        Runs every prediction through the deterministic validation layer.
        """
        if not contexts:
            return []

        # Generate deterministic rule candidates for validation
        rule_candidates_map = {
            idx: CandidateGenerator.generate_candidates(ctx)
            for idx, ctx in enumerate(contexts)
        }

        # Step 1: Query local Ollama/Qwen as the PRIMARY semantic classifier for ALL fields
        qwen_predictions_map: Dict[int, Dict[str, Any]] = {}
        if self.ollama_client and getattr(self.ollama_client, "is_available", False):
            batch_payload = []
            for idx, ctx in enumerate(contexts):
                batch_payload.append({
                    "field_id": idx,
                    "field": ctx.field_text,
                    "value": ctx.value_text,
                    "value_type": ctx.value_type,
                    "document_type": ctx.document_type,
                    "region_type": ctx.region_type,
                    "section": ctx.parent_region or "body",
                    "table_name": ctx.table_context.get("table_name") if ctx.table_context else None,
                    "table_column": ctx.column_name,
                    "table_row": ctx.row_context[:4] if ctx.row_context else [],
                    "nearby_fields": ctx.neighboring_fields[:5],
                    "nearby_values": ctx.neighboring_values[:5],
                    "nearby_text": ctx.nearby_text[:4]
                })

            raw_predictions = self.ollama_client.analyze_semantic_batch(batch_payload)
            if raw_predictions and isinstance(raw_predictions, list):
                for item in raw_predictions:
                    if isinstance(item, dict) and "field_id" in item:
                        try:
                            f_id = int(item["field_id"])
                            qwen_predictions_map[f_id] = item
                        except (ValueError, TypeError):
                            pass

        # Step 2: Run Validator Layer for every context
        results: List[SemanticFieldResult] = []
        for idx, ctx in enumerate(contexts):
            candidates = rule_candidates_map.get(idx, [])
            qwen_res = qwen_predictions_map.get(idx)

            res = self._validate_and_finalize(ctx, candidates, qwen_res)
            results.append(res)

        return results

    def _validate_and_finalize(
        self,
        context: SemanticContext,
        candidates: List[SemanticCandidate],
        qwen_result: Optional[Dict[str, Any]]
    ) -> SemanticFieldResult:
        top_candidate: Optional[SemanticCandidate] = candidates[0] if candidates else None

        qwen_identity: Optional[str] = None
        qwen_label: Optional[str] = None
        qwen_conf: float = 0.0

        if qwen_result and isinstance(qwen_result, dict):
            raw_id = str(qwen_result.get("identified_as") or "").strip().lower()
            if raw_id and raw_id in CANONICAL_ONTOLOGY:
                qwen_identity = raw_id
                qwen_label = CANONICAL_ONTOLOGY[raw_id].display_label
                qwen_conf = float(qwen_result.get("confidence", 0.90))

        semantic_source = "ollama" if qwen_identity else "fallback"
        final_identity = qwen_identity
        display_label = qwen_label or (top_candidate.display_label if top_candidate else "Unknown Field")
        semantic_conf = qwen_conf if qwen_identity else (top_candidate.confidence if top_candidate else 0.40)
        validation_notes: List[str] = []
        needs_review = False

        # --- VALIDATOR LAYER ---
        if qwen_identity:
            # Rule 1: Validate context contradiction (e.g. contact_number vs bank_account_number)
            nearby_str = " ".join([context.field_text] + context.neighboring_fields + context.nearby_text).lower()
            is_bank_context = any(k in nearby_str for k in ["bank", "account", "ifsc", "swift", "branch"])
            is_phone_context = any(k in nearby_str for k in ["phone", "mobile", "cell", "tel", "contact", "fax"])

            if qwen_identity in ["contact_number", "mobile_number", "telephone_number"] and is_bank_context and not is_phone_context:
                validation_notes.append("Validator penalized Qwen: Phone identity predicted in Bank Details section.")
                if top_candidate and top_candidate.canonical_name in ["bank_account_number", "account_holder_name", "ifsc_code"]:
                    final_identity = top_candidate.canonical_name
                    display_label = top_candidate.display_label
                    semantic_conf = max(top_candidate.confidence, 0.85)
                    validation_notes.append(f"Validator overridden to rule candidate '{final_identity}'.")
                    needs_review = True
                else:
                    final_identity = "bank_account_number"
                    display_label = "Bank Account Number"
                    semantic_conf = 0.75
                    needs_review = True

            # Rule 2: Strongly validated rule candidate match boosts Ollama prediction
            elif top_candidate and top_candidate.canonical_name == qwen_identity:
                validation_notes.append("Deterministic rule validated Qwen prediction.")
                semantic_conf = min(semantic_conf + 0.05, 0.99)

            # Rule 3: Contradiction check against high confidence deterministic rule candidate
            elif top_candidate and top_candidate.confidence >= 0.85 and top_candidate.canonical_name != qwen_identity:
                validation_notes.append(f"Qwen prediction '{qwen_identity}' contradicts strong rule candidate '{top_candidate.canonical_name}'.")
                needs_review = True
                if semantic_conf < 0.80:
                    final_identity = top_candidate.canonical_name
                    display_label = top_candidate.display_label
                    semantic_conf = top_candidate.confidence
                    validation_notes.append(f"Validator overridden to '{final_identity}'.")

            if not final_identity:
                final_identity = qwen_identity
        else:
            # Fallback when Ollama is offline or unhelpful
            if top_candidate:
                final_identity = top_candidate.canonical_name
                display_label = top_candidate.display_label
                semantic_conf = top_candidate.confidence
                validation_notes.append("Offline rule fallback selected.")
                needs_review = top_candidate.confidence < 0.60
            else:
                final_identity = "unknown_field"
                display_label = "Unknown Field"
                semantic_conf = 0.35
                validation_notes.append("Unknown field: insufficient evidence.")
                needs_review = True

        # Calculate final combined confidence score
        final_conf = round(
            context.ocr_confidence * 0.2 +
            context.grouping_confidence * 0.2 +
            semantic_conf * 0.6,
            4
        )
        final_conf = min(max(final_conf, 0.0), 1.0)

        evidence_dict = {
            "field_context": context.field_text,
            "value_type": context.value_type,
            "region_context": context.region_type,
            "table_context": f"{context.table_context.get('table_name')}:{context.column_name}" if context.table_context else context.column_name,
            "model_reason": f"ollama_qwen:{qwen_identity}" if qwen_identity else "deterministic_fallback",
            "validation_notes": validation_notes
        }

        return SemanticFieldResult(
            source_field=context.field_text,
            value=context.value_text,
            identified_as=final_identity,
            display_label=display_label,
            qwen_prediction=qwen_identity,
            final_prediction=final_identity,
            semantic_source=semantic_source,
            ocr_confidence=context.ocr_confidence,
            grouping_confidence=context.grouping_confidence,
            relationship_confidence=context.relationship_confidence,
            semantic_confidence=round(semantic_conf, 4),
            final_confidence=final_conf,
            evidence=validation_notes if validation_notes else [f"source:{semantic_source}"],
            evidence_details=evidence_dict,
            needs_review=needs_review,
            candidates=candidates[:5],
            bbox=context.bbox
        )

    def _fallback_classify(self, context: SemanticContext) -> SemanticFieldResult:
        candidates = CandidateGenerator.generate_candidates(context)
        return self._validate_and_finalize(context, candidates, qwen_result=None)
