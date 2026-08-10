"""DataExpert Day 2 deliverable: psycopg2-based weather embedding ingestion.

Run from the repository root in an environment that has the same Lakebase
connection environment variables as the Databricks App:

    python notebooks/ingest_weather_embeddings.py

Required environment variables:
    PGHOST, PGPORT, PGDATABASE, PGUSER, PGSSLMODE, ENDPOINT_NAME

The script deliberately uses psycopg2 + execute_values for the write path,
not Spark JDBC, matching the homework requirements.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer

from lakebase import ensure_weather_schema, get_connection

MODEL_NAME = os.environ.get(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/all-MiniLM-L6-v2",
)
EMBEDDING_DIM = 384
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "100"))


def chunk_text(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - CHUNK_OVERLAP
    return chunks


def vector_literal(vector) -> str:
    values = vector.tolist() if hasattr(vector, "tolist") else list(vector)
    if len(values) != EMBEDDING_DIM:
        raise ValueError(f"Expected {EMBEDDING_DIM} dimensions, got {len(values)}")
    return "[" + ",".join(f"{float(v):.9f}" for v in values) + "]"


def main() -> None:
    ensure_weather_schema()
    model = SentenceTransformer(MODEL_NAME)

    # Read unembedded rows through the same psycopg2 get_connection() helper
    # used by the Flask application.
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.id, d.narrative_text
                FROM public.weather_documents d
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM public.weather_embeddings e
                    WHERE e.document_id = d.id
                      AND e.model_name = %s
                )
                ORDER BY d.synced_at, d.id
                """,
                (MODEL_NAME,),
            )
            documents = cur.fetchall()

    if not documents:
        print("No unembedded weather documents found.")
        return

    rows = []
    for document in documents:
        chunks = chunk_text(document["narrative_text"])
        if not chunks:
            continue

        vectors = model.encode(
            chunks,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=32,
        )

        for chunk_index, (chunk, vector) in enumerate(zip(chunks, vectors)):
            rows.append((
                document["id"],
                chunk_index,
                chunk,
                vector_literal(vector),
                MODEL_NAME,
            ))

    # Batch write via psycopg2.extras.execute_values. The vector is passed as a
    # pgvector literal and explicitly cast with %s::vector in the SQL template.
    with get_connection() as conn:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO public.weather_embeddings (
                    document_id, chunk_index, chunk_text, embedding, model_name
                )
                VALUES %s
                ON CONFLICT (document_id, chunk_index, model_name)
                DO UPDATE SET
                    chunk_text = EXCLUDED.chunk_text,
                    embedding = EXCLUDED.embedding,
                    created_at = NOW()
                """,
                rows,
                template="(%s, %s, %s, %s::vector, %s)",
                page_size=100,
            )
        conn.commit()

    print(f"Documents processed: {len(documents)}")
    print(f"Chunks embedded: {len(rows)}")
    print(f"Model: {MODEL_NAME}")
    print(f"Dimensions: {EMBEDDING_DIM}")
    print(f"Chunk size: {CHUNK_SIZE}; overlap: {CHUNK_OVERLAP}")


if __name__ == "__main__":
    main()
