import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.schemas.intelligence_schema import (
    DocumentIntelligenceResult, StructuredInformationSummary
)

logger = logging.getLogger("DatabaseService")

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))

class DatabaseService:
    """
    SQLite Database Service for storing and querying EXCLUSIVELY extracted structured information.
    Original document files/binaries are NOT stored. Stores structured_data JSON and indexed entities.
    """
    DB_DIR = DB_DIR
    DB_PATH = os.path.join(DB_DIR, "document_intelligence.db")

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(cls.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        """Initializes SQLite database schema and indexes for structured information."""
        conn = cls.get_connection()
        cursor = conn.cursor()

        # 1. Main Structured Documents Knowledge Table (No raw file storage)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS structured_documents (
                id TEXT PRIMARY KEY,
                document_type TEXT NOT NULL,
                structured_data TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            );
        """)

        # 2. Relational Entity Index for SQL Querying
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extracted_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                key TEXT NOT NULL,
                label TEXT,
                raw_value TEXT,
                normalized_value TEXT,
                value_type TEXT,
                confidence REAL,
                source_page INTEGER DEFAULT 1,
                source_bbox_json TEXT,
                needs_review INTEGER DEFAULT 0,
                FOREIGN KEY (document_id) REFERENCES structured_documents (id) ON DELETE CASCADE
            );
        """)

        # 3. Document-Centric Dynamic Datasets Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_datasets (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                dataset_name TEXT NOT NULL,
                schema_json TEXT NOT NULL,
                header_row_json TEXT NOT NULL,
                table_rows_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES structured_documents (id) ON DELETE CASCADE
            );
        """)

        # Indexes for fast SQL search & filtering
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_struct_doc_type ON structured_documents (document_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_struct_created ON structured_documents (created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_doc ON extracted_entities (document_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_key ON extracted_entities (key);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_norm ON extracted_entities (normalized_value);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON extracted_entities (value_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dataset_doc ON document_datasets (document_id);")

        conn.commit()
        conn.close()
        logger.info(f"SQLite Structured Knowledge Database initialized at: {cls.DB_PATH}")

    @classmethod
    def save_document(
        cls,
        intel_result: DocumentIntelligenceResult,
        total_pages: int = 1,
        average_confidence: float = 0.0,
        raw_text: str = ""
    ) -> str:
        """
        Saves ONLY extracted structured document information into SQLite.
        Does NOT store persistent original binary or path references.
        """
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Insert into structured_documents table
        cursor.execute("""
            INSERT OR REPLACE INTO structured_documents (
                id, document_type, structured_data, confidence, created_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            intel_result.document_id,
            intel_result.document_type,
            json.dumps(intel_result.structured_json),
            intel_result.confidence_score or average_confidence,
            created_at,
            json.dumps({
                "total_pages": total_pages,
                "average_confidence": average_confidence,
                "entity_count": len(intel_result.entities),
                "table_count": len(intel_result.tables)
            })
        ))

        # 2. Insert extracted entity index
        for entity in intel_result.entities:
            source_bbox_str = json.dumps(entity.source.bbox) if entity.source else "[]"
            source_pg = entity.source.page if entity.source else 1

            cursor.execute("""
                INSERT INTO extracted_entities (
                    document_id, key, label, raw_value, normalized_value,
                    value_type, confidence, source_page, source_bbox_json, needs_review
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                intel_result.document_id,
                entity.key,
                entity.label,
                entity.raw_value,
                str(entity.normalized_value) if entity.normalized_value is not None else entity.raw_value,
                entity.value_type,
                entity.confidence,
                source_pg,
                source_bbox_str,
                1 if entity.needs_review else 0
            ))

        # 3. Insert Document-Centric Dynamic Dataset Table Representation
        dyn_dataset = intel_result.structured_json.get("dynamic_dataset", {})
        if dyn_dataset:
            cursor.execute("""
                INSERT OR REPLACE INTO document_datasets (
                    id, document_id, dataset_name, schema_json, header_row_json, table_rows_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                dyn_dataset.get("dataset_id", f"dataset_{intel_result.document_id}"),
                intel_result.document_id,
                dyn_dataset.get("title", f"{intel_result.document_type.upper()}_Dataset"),
                json.dumps(dyn_dataset.get("columns", [])),
                json.dumps(dyn_dataset.get("header_record", {})),
                json.dumps(dyn_dataset.get("table_rows", [])),
                created_at
            ))

        conn.commit()
        conn.close()
        logger.info(f"Extracted structured knowledge (ID '{intel_result.document_id}') saved to SQLite.")
        return intel_result.document_id

    @classmethod
    def get_documents(
        cls,
        document_type: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 50
    ) -> List[StructuredInformationSummary]:
        """Fetches stored structured information summaries from SQLite."""
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()

        sql = """
            SELECT 
                d.id, d.document_type, d.structured_data, d.confidence, d.created_at, d.metadata,
                COUNT(DISTINCT e.id) as entity_count,
                SUM(CASE WHEN e.needs_review = 1 THEN 1 ELSE 0 END) as needs_review_count
            FROM structured_documents d
            LEFT JOIN extracted_entities e ON d.id = e.document_id
        """

        params = []
        where_clauses = []

        if document_type and document_type.lower() != "all":
            where_clauses.append("LOWER(d.document_type) = LOWER(?)")
            params.append(document_type)

        if search_query and search_query.strip():
            where_clauses.append("(LOWER(d.structured_data) LIKE ? OR LOWER(e.raw_value) LIKE ?)")
            q = f"%{search_query.strip().lower()}%"
            params.extend([q, q])

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        sql += " GROUP BY d.id ORDER BY d.created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        summaries: List[StructuredInformationSummary] = []
        for r in rows:
            structured = {}
            meta = {}
            try:
                structured = json.loads(r["structured_data"])
                if r["metadata"]:
                    meta = json.loads(r["metadata"])
            except Exception:
                pass

            title_highlight = structured.get("title_highlight") or f"{r['document_type'].replace('_', ' ').upper()} Record"
            key_highlights = structured.get("key_highlights") or {}

            summaries.append(StructuredInformationSummary(
                id=r["id"],
                document_type=r["document_type"],
                title_highlight=title_highlight,
                created_at=r["created_at"],
                total_pages=meta.get("total_pages", 1),
                average_confidence=round(r["confidence"] * 100 if r["confidence"] <= 1.0 else r["confidence"], 1),
                entity_count=r["entity_count"] or 0,
                table_count=meta.get("table_count", 0),
                needs_review_count=r["needs_review_count"] or 0,
                key_highlights=key_highlights
            ))

        return summaries

    @classmethod
    def get_document_by_id(cls, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves full extracted structured information payload by ID."""
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM structured_documents WHERE id = ?", (doc_id,))
        doc_row = cursor.fetchone()
        if not doc_row:
            conn.close()
            return None

        # Retrieve indexed entities
        cursor.execute("SELECT * FROM extracted_entities WHERE document_id = ?", (doc_id,))
        entity_rows = cursor.fetchall()

        conn.close()

        structured = json.loads(doc_row["structured_data"])
        
        return {
            "document_id": doc_row["id"],
            "document_type": doc_row["document_type"],
            "created_at": doc_row["created_at"],
            "confidence": doc_row["confidence"],
            "structured_json": structured,
            "entities": [dict(e) for e in entity_rows],
        }

    @classmethod
    def delete_document(cls, doc_id: str) -> bool:
        """Deletes structured document entry and cascade entity indices."""
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM structured_documents WHERE id = ?", (doc_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    @classmethod
    def get_document_dataset(cls, doc_id: str) -> Optional[Dict[str, Any]]:
        """Fetches stored Document-Centric Dynamic Table Dataset representation by document ID."""
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM document_datasets WHERE document_id = ?", (doc_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "dataset_id": row["id"],
            "document_id": row["document_id"],
            "dataset_name": row["dataset_name"],
            "columns": json.loads(row["schema_json"]),
            "header_record": json.loads(row["header_row_json"]),
            "table_rows": json.loads(row["table_rows_json"]),
            "created_at": row["created_at"]
        }
