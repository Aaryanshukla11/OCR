import re
import sqlite3
import logging
from typing import List, Dict, Any, Optional

from app.services.database import DatabaseService
from app.schemas.intelligence_schema import (
    QueryPlan, QueryResponse, StoredDocumentSummary, ExtractedEntity, SourceProvenance
)

logger = logging.getLogger("DocumentQueryEngine")

class DocumentQueryEngine:
    """
    Natural Language Query & Information Retrieval Engine.
    Translates user questions into validated, parameterized SQLite queries,
    performs aggregations (SUM, COUNT, AVG), and returns structured answers with document provenance.
    """

    @classmethod
    def execute_query(cls, user_query: str) -> QueryResponse:
        """Main entry point: Executes a natural language query against stored SQLite document intelligence."""
        plan = cls.understand_query(user_query)
        return cls._run_query_plan(user_query, plan)

    @classmethod
    def understand_query(cls, query: str) -> QueryPlan:
        """
        Query Understanding Layer: Translates natural language into a Structured Query Plan.
        """
        q_lower = query.lower().strip()

        target_type = None
        field_key = None
        aggregation = "NONE"
        search_terms = []
        date_start = None
        date_end = None

        # 1. Detect Document Type Intent
        if "invoice" in q_lower or "bill" in q_lower:
            target_type = "invoice"
        elif "flight" in q_lower or "ticket" in q_lower or "pnr" in q_lower or "boarding" in q_lower:
            target_type = "flight_ticket"
        elif "receipt" in q_lower or "food" in q_lower or "restaurant" in q_lower:
            target_type = "receipt"
        elif "hotel" in q_lower:
            target_type = "hotel_invoice"
        elif "bank" in q_lower or "statement" in q_lower:
            target_type = "bank_statement"
        elif "medical" in q_lower or "report" in q_lower or "patient" in q_lower:
            target_type = "medical_report"
        elif "contract" in q_lower or "agreement" in q_lower:
            target_type = "contract"

        # 2. Detect Aggregation Intent
        if any(w in q_lower for w in ["how much", "total spend", "total amount", "sum of", "total cost"]):
            aggregation = "SUM"
            field_key = "total"
        elif any(w in q_lower for w in ["how many", "count of", "number of"]):
            aggregation = "COUNT"
        elif "average" in q_lower or "avg" in q_lower:
            aggregation = "AVG"
            field_key = "total"
        elif "maximum" in q_lower or "highest" in q_lower or "max" in q_lower:
            aggregation = "MAX"
            field_key = "total"
        elif "minimum" in q_lower or "lowest" in q_lower or "min" in q_lower:
            aggregation = "MIN"
            field_key = "total"

        # 3. Detect Specific Field Intent
        if "gst" in q_lower or "tax id" in q_lower or "gstin" in q_lower:
            field_key = "gstin"
        elif "pnr" in q_lower:
            field_key = "pnr_number"
        elif "date" in q_lower:
            field_key = "date"

        # 4. Detect Date Range (e.g. "August", "2026")
        if "august" in q_lower or "aug" in q_lower:
            date_start = "2026-08-01"
            date_end = "2026-08-31"
        elif "july" in q_lower:
            date_start = "2026-07-01"
            date_end = "2026-07-31"

        # 5. Extract Named Entity Search Terms
        # Remove common stop words
        stop_words = {"show", "me", "all", "invoices", "receipts", "flights", "documents", "from", "the", "which", "did", "take", "in", "august", "give", "gst", "number", "of", "find", "how", "much", "spend", "on", "food", "who", "what", "is", "a"}
        words = re.findall(r"\b[A-Za-z0-9]+\b", query)
        for w in words:
            if w.lower() not in stop_words and len(w) >= 3:
                search_terms.append(w)

        return QueryPlan(
            query_text=query,
            target_document_type=target_type,
            field_key=field_key,
            date_start=date_start,
            date_end=date_end,
            search_terms=search_terms,
            aggregation=aggregation
        )

    @classmethod
    def _run_query_plan(cls, original_query: str, plan: QueryPlan) -> QueryResponse:
        """Executes safe parameterized SQL query against SQLite database."""
        conn = DatabaseService.get_connection()
        cursor = conn.cursor()

        # Build SQL query dynamically and safely using parameters
        sql = """
            SELECT 
                d.id as doc_id, d.filename, d.document_type, d.created_at, d.total_pages, d.average_confidence,
                e.key, e.label, e.raw_value, e.normalized_value, e.value_type, e.confidence, e.source_page, e.source_bbox_json
            FROM documents d
            LEFT JOIN document_entities e ON d.id = e.document_id
        """

        where_conditions = []
        params = []

        if plan.target_document_type:
            where_conditions.append("LOWER(d.document_type) = LOWER(?)")
            params.append(plan.target_document_type)

        if plan.date_start and plan.date_end:
            where_conditions.append("(d.created_at BETWEEN ? AND ? OR e.normalized_value BETWEEN ? AND ?)")
            params.extend([f"{plan.date_start} 00:00:00", f"{plan.date_end} 23:59:59", plan.date_start, plan.date_end])

        if plan.search_terms:
            term_clauses = []
            for term in plan.search_terms:
                term_clauses.append("(LOWER(d.filename) LIKE ? OR LOWER(d.raw_text) LIKE ? OR LOWER(e.raw_value) LIKE ?)")
                p = f"%{term.lower()}%"
                params.extend([p, p, p])
            where_conditions.append("(" + " OR ".join(term_clauses) + ")")

        if where_conditions:
            sql += " WHERE " + " AND ".join(where_conditions)

        sql += " ORDER BY d.created_at DESC LIMIT 100"

        plan.sql_executed = sql
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        # Process Results
        matched_doc_ids = set()
        matched_doc_summaries: Dict[str, StoredDocumentSummary] = {}
        matching_entities: List[ExtractedEntity] = []
        numeric_values: List[float] = []

        for r in rows:
            doc_id = r["doc_id"]
            matched_doc_ids.add(doc_id)

            if doc_id not in matched_doc_summaries:
                matched_doc_summaries[doc_id] = StoredDocumentSummary(
                    id=doc_id,
                    filename=r["filename"],
                    document_type=r["document_type"],
                    created_at=r["created_at"],
                    total_pages=r["total_pages"],
                    average_confidence=r["average_confidence"],
                    entity_count=0,
                    table_count=0,
                    needs_review_count=0
                )

            if r["key"]:
                bbox_list = []
                try:
                    if r["source_bbox_json"]:
                        bbox_list = json.loads(r["source_bbox_json"])
                except Exception:
                    pass

                entity = ExtractedEntity(
                    key=r["key"],
                    label=r["label"] or r["key"],
                    raw_value=r["raw_value"] or "",
                    normalized_value=r["normalized_value"],
                    value_type=r["value_type"] or "string",
                    confidence=r["confidence"] or 1.0,
                    source=SourceProvenance(page=r["source_page"] or 1, bbox=bbox_list, text=r["raw_value"] or "")
                )
                matching_entities.append(entity)

                # Collect numeric values for aggregation if requested
                if plan.aggregation != "NONE":
                    norm_val = r["normalized_value"]
                    if norm_val:
                        try:
                            # Extract numeric float
                            cleaned_num = re.sub(r"[^\d.]", "", str(norm_val))
                            if cleaned_num:
                                numeric_values.append(float(cleaned_num))
                        except ValueError:
                            pass

        # Calculate Aggregations
        agg_result = None
        if plan.aggregation == "SUM" and numeric_values:
            agg_result = round(sum(numeric_values), 2)
        elif plan.aggregation == "COUNT":
            agg_result = len(matched_doc_ids)
        elif plan.aggregation == "AVG" and numeric_values:
            agg_result = round(sum(numeric_values) / len(numeric_values), 2)
        elif plan.aggregation == "MAX" and numeric_values:
            agg_result = max(numeric_values)
        elif plan.aggregation == "MIN" and numeric_values:
            agg_result = min(numeric_values)

        # Generate Natural Answer Summary
        doc_count = len(matched_doc_ids)
        if doc_count == 0:
            summary_text = f"No documents matched your query: '{original_query}'."
        else:
            summary_text = f"Found {doc_count} document(s) matching your query."
            if agg_result is not None:
                summary_text += f" Calculated {plan.aggregation}: {agg_result}"

        return QueryResponse(
            query=original_query,
            plan=plan,
            answer_summary=summary_text,
            total_matches=doc_count,
            aggregated_value=agg_result,
            documents=list(matched_doc_summaries.values()),
            matching_entities=matching_entities[:25]
        )
