"""Lakebase connection and DDL helpers for the weather vector homework.

The Databricks App database resource injects PGHOST, PGPORT, PGDATABASE,
PGUSER and PGSSLMODE. A short-lived OAuth database credential is generated
for every new psycopg2 connection, so no database password is stored in code.
"""

import os
from contextlib import contextmanager

import psycopg2
from databricks.sdk import WorkspaceClient
from psycopg2.extras import Json, RealDictCursor, execute_values

_w = WorkspaceClient()

WEATHER_DOCUMENTS_DDL = """
CREATE TABLE IF NOT EXISTS public.weather_documents (
    id TEXT PRIMARY KEY,
    location TEXT NOT NULL,
    source_type TEXT NOT NULL
        CHECK (source_type IN ('alert', 'forecast')),
    headline TEXT,
    narrative_text TEXT NOT NULL,
    issued_at TIMESTAMPTZ,
    effective_at TIMESTAMPTZ,
    payload JSONB NOT NULL,
    synced_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""

WEATHER_EMBEDDINGS_DDL = """
CREATE TABLE IF NOT EXISTS public.weather_embeddings (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id TEXT NOT NULL
        REFERENCES public.weather_documents(id)
        ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    chunk_text TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    model_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, chunk_index, model_name)
)
"""

HNSW_INDEX_DDL = """
CREATE INDEX IF NOT EXISTS weather_embeddings_hnsw_idx
ON public.weather_embeddings
USING hnsw (embedding vector_cosine_ops)
"""


def _database_token() -> str:
    endpoint_name = os.environ["ENDPOINT_NAME"]
    credential = _w.postgres.generate_database_credential(endpoint=endpoint_name)
    return credential.token


@contextmanager
def get_connection():
    """Yield a psycopg2 connection using the Databricks App OAuth identity."""
    conn = psycopg2.connect(
        host=os.environ["PGHOST"],
        port=int(os.environ.get("PGPORT", "5432")),
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=_database_token(),
        sslmode=os.environ.get("PGSSLMODE", "require"),
        connect_timeout=15,
        cursor_factory=RealDictCursor,
    )
    try:
        yield conn
    finally:
        conn.close()


def run_query(sql: str, params: tuple | list | None = None) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


def run_write(sql: str, params: tuple | list | None = None) -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            affected = cur.rowcount
        conn.commit()
        return affected


def ensure_weather_schema() -> None:
    """Create the two homework tables and the cosine HNSW index.

    Lakebase Search / pgvector must already be enabled in the project so the
    VECTOR type and hnsw access method exist.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(WEATHER_DOCUMENTS_DDL)
            cur.execute(WEATHER_EMBEDDINGS_DDL)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_weather_documents_location "
                "ON public.weather_documents(location)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_weather_documents_source_type "
                "ON public.weather_documents(source_type)"
            )
            cur.execute(HNSW_INDEX_DDL)
        conn.commit()


def upsert_weather_documents(documents: list[dict]) -> int:
    """Batch upsert normalized NWS documents using psycopg2.execute_values."""
    if not documents:
        return 0

    rows = [
        (
            doc["id"],
            doc["location"],
            doc["source_type"],
            doc.get("headline"),
            doc["narrative_text"],
            doc.get("issued_at"),
            doc.get("effective_at"),
            Json(doc["payload"]),
        )
        for doc in documents
    ]

    sql = """
        INSERT INTO public.weather_documents (
            id, location, source_type, headline, narrative_text,
            issued_at, effective_at, payload, synced_at
        )
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            location = EXCLUDED.location,
            source_type = EXCLUDED.source_type,
            headline = EXCLUDED.headline,
            narrative_text = EXCLUDED.narrative_text,
            issued_at = EXCLUDED.issued_at,
            effective_at = EXCLUDED.effective_at,
            payload = EXCLUDED.payload,
            synced_at = NOW()
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            execute_values(
                cur,
                sql,
                rows,
                template="(%s, %s, %s, %s, %s, %s, %s, %s, NOW())",
                page_size=200,
            )
        conn.commit()

    return len(rows)
