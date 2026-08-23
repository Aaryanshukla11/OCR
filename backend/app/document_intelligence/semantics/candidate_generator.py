import re
from typing import List, Dict, Any
from app.document_intelligence.semantics.models import SemanticContext, SemanticCandidate
from app.document_intelligence.semantics.ontology import CANONICAL_ONTOLOGY, ValueType

class CandidateGenerator:
    """
    Generates candidate semantic identities and evidence features by evaluating
    field label aliases, value type compatibility, and regional context.
    """

    @staticmethod
    def _clean_token(text: str) -> str:
        s = text.lower().strip()
        s = re.sub(r'[^\w\s]', '', s)
        return s

    @staticmethod
    def generate_candidates(context: SemanticContext) -> List[SemanticCandidate]:
        candidates: List[SemanticCandidate] = []
        field_clean = CandidateGenerator._clean_token(context.field_text)
        val_type = context.value_type

        for key, entry in CANONICAL_ONTOLOGY.items():
            if key == "unknown_field":
                continue

            score = 0.0
            evidence_list: List[str] = []

            # 1. Direct or Alias Match
            alias_match_found = False
            for alias in entry.aliases:
                alias_clean = CandidateGenerator._clean_token(alias)
                alias_words = alias_clean.split()
                field_words = field_clean.split()
                if field_clean == alias_clean:
                    score += 0.85
                    evidence_list.append(f"exact-alias-match: '{alias}'")
                    alias_match_found = True
                    break
                elif len(alias_words) == 1 and alias_words[0] in field_words and len(alias_words[0]) > 2:
                    score += 0.65
                    evidence_list.append(f"word-alias-match: '{alias}'")
                    alias_match_found = True
                    break
                elif len(alias_words) > 1 and alias_clean in field_clean:
                    score += 0.65
                    evidence_list.append(f"phrase-alias-match: '{alias}'")
                    alias_match_found = True
                    break

            # 2. Value Type Compatibility Match
            val_type_enum = None
            try:
                val_type_enum = ValueType(val_type)
            except ValueError:
                pass

            if val_type_enum and val_type_enum in entry.compatible_value_types:
                if val_type_enum in (ValueType.GSTIN, ValueType.PAN, ValueType.IFSC, ValueType.EMAIL, ValueType.PHONE_NUMBER, ValueType.URL, ValueType.CURRENCY, ValueType.DATE):
                    score += 0.65
                    evidence_list.append(f"high-precision-value-pattern: {val_type}")
                else:
                    score += 0.25
                    evidence_list.append(f"value-type-compatible: {val_type}")
            elif val_type_enum and val_type_enum not in (ValueType.UNKNOWN, ValueType.TEXT):
                # Penalty if value type contradicts candidate
                score -= 0.30

            # 3. Contextual / Regional Evidence Boost
            # Account / Bank context
            if key in ("bank_account_number", "bank_account_name", "ifsc_code", "bank_name"):
                if any(w in field_clean for w in ["acc", "account", "bank", "ifsc", "a/c"]):
                    score += 0.15
                    evidence_list.append("banking-keyword-evidence")

            # Travel / Ticket context
            if key in ("travel_date", "ticket_number", "flight_number", "passenger_name"):
                if any(w in field_clean for w in ["travel", "ticket", "pnr", "flight", "pax", "passenger", "booked"]):
                    score += 0.15
                    evidence_list.append("travel-keyword-evidence")

            # GST / Tax context
            if key in ("gstin", "pan", "cin", "cgst_amount", "sgst_amount", "igst_amount"):
                if any(w in field_clean for w in ["gst", "pan", "cin", "tax"]):
                    score += 0.15
                    evidence_list.append("tax-keyword-evidence")

            if score > 0.30:
                final_conf = min(round(score, 4), 0.99)
                candidates.append(SemanticCandidate(
                    canonical_name=key,
                    display_label=entry.display_label,
                    confidence=final_conf,
                    evidence=evidence_list,
                    candidate_type="rule_candidate"
                ))

        # Sort candidates descending by confidence score
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        return candidates
