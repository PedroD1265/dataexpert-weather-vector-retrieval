-- DataExpert Day 2 Homework: Weather Intelligence schema
-- Run as a Lakebase project owner if you want to create the schema manually.
-- The Flask app also contains equivalent CREATE TABLE IF NOT EXISTS migrations.

-- On Lakebase Autoscaling with Lakebase Search enabled, this installs
-- lakebase_vector and pgvector compatibility. If already enabled, it is a no-op.
CREATE EXTENSION IF NOT EXISTS lakebase_vector CASCADE;

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

CREATE INDEX IF NOT EXISTS idx_weather_documents_location
    ON public.weather_documents(location);

CREATE INDEX IF NOT EXISTS idx_weather_documents_source_type
    ON public.weather_documents(source_type);

CREATE INDEX IF NOT EXISTS weather_embeddings_hnsw_idx
    ON public.weather_embeddings
    USING hnsw (embedding vector_cosine_ops);

-- Verification queries useful for submission screenshots.
-- SELECT COUNT(*) FROM public.weather_documents;
-- SELECT COUNT(*) FROM public.weather_embeddings;
-- SELECT indexname, indexdef FROM pg_indexes
-- WHERE tablename = 'weather_embeddings';
