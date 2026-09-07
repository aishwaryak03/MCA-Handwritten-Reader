import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import DATA_DIR, MONGO_URI, MONGO_DB

SQLITE_DB = DATA_DIR / "app.db"


class Database:
    def __init__(self):
        self.mongo = None
        self.collection = None
        if MONGO_URI:
            try:
                from pymongo import MongoClient
                client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1200)
                client.admin.command("ping")
                self.mongo = client
                self.collection = client[MONGO_DB]["documents"]
            except Exception:
                self.mongo = None
                self.collection = None

        if self.collection is None:
            self._init_sqlite()

    @property
    def backend_name(self):
        return "MongoDB" if self.collection is not None else "SQLite"

    def _connect_sqlite(self):
        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self):
        with self._connect_sqlite() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    language TEXT,
                    confidence REAL,
                    ocr_text TEXT,
                    extracted_json TEXT,
                    created_at TEXT
                )
            """)
            conn.commit()

    def insert_document(self, doc):
        if self.collection is not None:
            result = self.collection.insert_one(doc)
            return str(result.inserted_id)

        with self._connect_sqlite() as conn:
            conn.execute(
                """INSERT INTO documents
                   (id, filename, language, confidence, ocr_text, extracted_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    doc["id"],
                    doc["filename"],
                    doc["language"],
                    doc["confidence"],
                    doc["ocr_text"],
                    json.dumps(doc["extracted"], ensure_ascii=False),
                    doc["created_at"],
                ),
            )
            conn.commit()
        return doc["id"]

    def _sqlite_row_to_doc(self, row):
        if not row:
            return None
        return {
            "id": row["id"],
            "filename": row["filename"],
            "language": row["language"],
            "confidence": row["confidence"],
            "ocr_text": row["ocr_text"],
            "extracted": json.loads(row["extracted_json"] or "{}"),
            "created_at": row["created_at"],
        }

    def get_document(self, doc_id):
        if self.collection is not None:
            doc = self.collection.find_one({"id": doc_id})
            if not doc:
                return None
            doc.pop("_id", None)
            return doc

        with self._connect_sqlite() as conn:
            row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return self._sqlite_row_to_doc(row)

    def list_documents(self, limit=50):
        if self.collection is not None:
            docs = list(self.collection.find({}, {"_id": 0}).sort("created_at", -1).limit(limit))
            return docs

        with self._connect_sqlite() as conn:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._sqlite_row_to_doc(row) for row in rows]


db = Database()


def now_iso():
    return datetime.now(timezone.utc).isoformat()
