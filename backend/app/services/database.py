import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from app.schemas.intelligence_schema import (
    DocumentIntelligenceResult, StoredDocumentSummary, ExtractedEntity, ExtractedTable
)

logger = logging.getLogger("DatabaseService")

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
class DatabaseService:
    """
    SQLite Database Service for storing and indexing structured document intelligence.
    Keeps database schemas document-agnostic. Stores raw text, full structured JSON,
    and indexed relational tables for fast parameter SQL querying.
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
        """Initializes SQLite database schema and indexes."""
        conn = cls.get_connection()
        cursor = conn.cursor()

        # 1. Main Documents Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                document_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_pages INTEGER DEFAULT 1,
                average_confidence REAL DEFAULT 0.0,
                raw_text TEXT,
                structured_json TEXT NOT NULL,
                metadata_json TEXT
            );
        """)

        # 2. Indexed Relational Entities Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_entities (
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
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            );
        """)

        # 3. Indexed Relational Tables Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                page_number INTEGER DEFAULT 1,
                headers_json TEXT,
                rows_json TEXT,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            );
        """)

        # Indexes for fast SQL search & filtering
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_type ON documents (document_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_created ON documents (created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_doc ON document_entities (document_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_key ON document_entities (key);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_norm ON document_entities (normalized_value);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON document_entities (value_type);")

        conn.commit()
        conn.close()
        logger.info(f"SQLite Document Intelligence Database initialized at: {cls.DB_PATH}")

    @classmethod
    def save_document(
        cls,
        intel_result: DocumentIntelligenceResult,
        total_pages: int,
        average_confidence: float,
        raw_text: str
    ) -> str:
        """Saves a document intelligence result into SQLite database."""
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Insert into documents table
        cursor.execute("""
            INSERT OR REPLACE INTO documents (
                id, filename, document_type, created_at, total_pages,
                average_confidence, raw_text, structured_json, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            intel_result.document_id,
            intel_result.filename,
            intel_result.document_type,
            created_at,
            total_pages,
            average_confidence,
            raw_text,
            json.dumps(intel_result.structured_json),
            json.dumps({"confidence_score": intel_result.confidence_score})
        ))

        # 2. Insert extracted entities
        for entity in intel_result.entities:
            source_bbox_str = json.dumps(entity.source.bbox) if entity.source else "[]"
            source_pg = entity.source.page if entity.source else 1

            cursor.execute("""
                INSERT INTO document_entities (
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

        # 3. Insert tables
        for tbl in intel_result.tables:
            cursor.execute("""
                INSERT INTO document_tables (
                    document_id, page_number, headers_json, rows_json
                ) VALUES (?, ?, ?, ?)
            """, (
                intel_result.document_id,
                tbl.page_number,
                json.dumps(tbl.headers),
                json.dumps(tbl.rows)
            ))

        conn.commit()
        conn.close()
        logger.info(f"Document '{intel_result.filename}' saved to SQLite with ID '{intel_result.document_id}'")
        return intel_result.document_id

    @classmethod
    def get_documents(
        cls,
        document_type: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 50
    ) -> List[StoredDocumentSummary]:
        """Fetches stored document summaries from SQLite database."""
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()

        sql = """
            SELECT 
                d.id, d.filename, d.document_type, d.created_at, d.total_pages, d.average_confidence,
                COUNT(DISTINCT e.id) as entity_count,
                COUNT(DISTINCT t.id) as table_count,
                SUM(CASE WHEN e.needs_review = 1 THEN 1 ELSE 0 END) as needs_review_count
            FROM documents d
            LEFT JOIN document_entities e ON d.id = e.document_id
            LEFT JOIN document_tables t ON d.id = t.document_id
        """

        params = []
        where_clauses = []

        if document_type and document_type.lower() != "all":
            where_clauses.append("LOWER(d.document_type) = LOWER(?)")
            params.append(document_type)

        if search_query and search_query.strip():
            where_clauses.append("(LOWER(d.filename) LIKE ? OR LOWER(d.raw_text) LIKE ?)")
            q = f"%{search_query.strip().lower()}%"
            params.extend([q, q])

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        sql += " GROUP BY d.id ORDER BY d.created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        summaries: List[StoredDocumentSummary] = []
        for r in rows:
            summaries.append(StoredDocumentSummary(
                id=r["id"],
                filename=r["filename"],
                document_type=r["document_type"],
                created_at=r["created_at"],
                total_pages=r["total_pages"],
                average_confidence=r["average_confidence"],
                entity_count=r["entity_count"] or 0,
                table_count=r["table_count"] or 0,
                needs_review_count=r["needs_review_count"] or 0
            ))

        return summaries

    @classmethod
    def get_document_by_id(cls, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves full document intelligence payload by document ID."""
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        doc_row = cursor.fetchone()
        if not doc_row:
            conn.close()
            return None

        # Retrieve entities
        cursor.execute("SELECT * FROM document_entities WHERE document_id = ?", (doc_id,))
        entity_rows = cursor.fetchall()

        # Retrieve tables
        cursor.execute("SELECT * FROM document_tables WHERE document_id = ?", (doc_id,))
        table_rows = cursor.fetchall()

        conn.close()

        structured = json.loads(doc_row["structured_json"])
        
        return {
            "document_id": doc_row["id"],
            "filename": doc_row["filename"],
            "document_type": doc_row["document_type"],
            "created_at": doc_row["created_at"],
            "total_pages": doc_row["total_pages"],
            "average_confidence": doc_row["average_confidence"],
            "raw_text": doc_row["raw_text"],
            "structured_json": structured,
            "entities": [dict(e) for e in entity_rows],
            "tables": [dict(t) for t in table_rows],
        }

    @classmethod
    def delete_document(cls, doc_id: str) -> bool:
        """Deletes document and cascade entity records."""
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
