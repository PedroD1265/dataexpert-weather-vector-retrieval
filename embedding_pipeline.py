"""Chunk and embed weather narratives, then write pgvector rows via psycopg2."""

from __future__ import annotations

import os

from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer

import lakebase

EMBEDDING_MODEL_NAME = os.environ.get(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/all-MiniLM-L6-v2",
)
EMBEDDING_DIM = 384
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "100"))

_MODEL: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Load the sentence-transformers model once per app process."""
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _MODEL


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Character sliding-window chunking with overlap."""
    text = (text or "").strip()
    if not text:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size")

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_length:
            break
        start = end - overlap

    return chunks


def _vector_literal(vector) -> str:
    values = vector.tolist() if hasattr(vector, "tolist") else list(vector)
    if len(values) != EMBEDDING_DIM:
        raise ValueError(
            f"Expected {EMBEDDING_DIM} dimensions, got {len(values)}"
        )
    return "[" + ",".join(f"{float(value):.9f}" for value in values) + "]"


def embed_query(query: str) -> str:
    model = get_model()
    vector = model.encode(
        query,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return _vector_literal(vector)


def embed_pending_documents(limit: int | None = None, batch_size: int = 100) -> dict:
    """Embed weather documents that do not yet have rows for this model."""
    lakebase.ensure_weather_schema()

    sql = """
        SELECT d.id, d.narrative_text
        FROM public.weather_documents d
        WHERE NOT EXISTS (
            SELECT 1
            FROM public.weather_embeddings e
            WHERE e.document_id = d.id
              AND e.model_name = %s
        )
        ORDER BY d.synced_at, d.id
    """
    params: list = [EMBEDDING_MODEL_NAME]
    if limit is not None:
        sql += " LIMIT %s"
        params.append(limit)

    documents = lakebase.run_query(sql, tuple(params))
    if not documents:
        return {
            "documents_processed": 0,
            "chunks_embedded": 0,
            "model": EMBEDDING_MODEL_NAME,
            "dimensions": EMBEDDING_DIM,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "message": "No unembedded weather documents found.",
        }

    model = get_model()
    total_chunks = 0

    with lakebase.get_connection() as conn:
        with conn.cursor() as cur:
            pending_rows = []

            def flush_rows():
                nonlocal pending_rows
                if not pending_rows:
                    return
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
                    pending_rows,
                    template="(%s, %s, %s, %s::vector, %s)",
                    page_size=batch_size,
                )
                pending_rows = []

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
                    pending_rows.append((
                        document["id"],
                        chunk_index,
                        chunk,
                        _vector_literal(vector),
                        EMBEDDING_MODEL_NAME,
                    ))
                    total_chunks += 1

                    if len(pending_rows) >= batch_size:
                        flush_rows()

            flush_rows()
        conn.commit()

    return {
        "documents_processed": len(documents),
        "chunks_embedded": total_chunks,
        "model": EMBEDDING_MODEL_NAME,
        "dimensions": EMBEDDING_DIM,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }
