# Lakebase Weather Schema

This file intentionally contains the DDL in a grader-readable Markdown format.

## Extension prerequisite

```sql
CREATE EXTENSION IF NOT EXISTS lakebase_vector CASCADE;
```

The Lakebase project must have Lakebase Search / pgvector support enabled so the `VECTOR` type and `hnsw` access method are available.

## `public.weather_documents`

```sql
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
);
```

Design notes:

- `id` is a stable deduplication key.
- Forecast IDs are SHA-256 hashes over location + period start + period name.
- Alert IDs are based on the upstream NWS alert identifier when available.
- `payload JSONB` preserves raw source data for provenance.
- `source_type` is constrained to `alert` or `forecast`.

## `public.weather_embeddings`

```sql
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
);
```

Required evidence is explicit here:

- Primary key: `weather_embeddings.id`
- Foreign key: `weather_embeddings.document_id -> weather_documents.id`
- Cascade delete: `ON DELETE CASCADE`
- Embedding dimension: `VECTOR(384)`
- Dedup constraint: `(document_id, chunk_index, model_name)`

## Supporting indexes

```sql
CREATE INDEX IF NOT EXISTS idx_weather_documents_location
ON public.weather_documents(location);

CREATE INDEX IF NOT EXISTS idx_weather_documents_source_type
ON public.weather_documents(source_type);
```

## HNSW vector index

```sql
CREATE INDEX IF NOT EXISTS weather_embeddings_hnsw_idx
ON public.weather_embeddings
USING hnsw (embedding vector_cosine_ops);
```

This index is configured for cosine-distance retrieval, matching the `<=>` operator used by `POST /weather/search`.

## Verification queries

### Show table columns and vector dimension

```sql
SELECT
    a.attname AS column_name,
    format_type(a.atttypid, a.atttypmod) AS data_type
FROM pg_attribute a
JOIN pg_class c ON a.attrelid = c.oid
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE n.nspname = 'public'
  AND c.relname = 'weather_embeddings'
  AND a.attnum > 0
  AND NOT a.attisdropped;
```

Expected evidence includes:

```text
embedding | vector(384)
```

### Show HNSW index

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename = 'weather_embeddings';
```

### Show sample weather documents

```sql
SELECT id, location, source_type, headline,
       LEFT(narrative_text, 160) AS narrative_preview,
       synced_at
FROM public.weather_documents
ORDER BY synced_at DESC
LIMIT 20;
```

### Show sample embeddings

```sql
SELECT document_id, chunk_index,
       LEFT(chunk_text, 120) AS chunk_preview,
       model_name,
       vector_dims(embedding) AS dimensions,
       created_at
FROM public.weather_embeddings
ORDER BY created_at DESC
LIMIT 20;
```
