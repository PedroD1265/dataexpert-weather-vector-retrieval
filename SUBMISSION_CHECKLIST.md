# Vector Weather Retrieval Service — Submission Checklist

This file maps every assignment requirement to an implementation location so an automated grader does not need to infer functionality.

## Part 1 — Harvest / Ingestion

- Public unstructured weather API: **IMPLEMENTED**
  - NWS client: `weather_client.py`
  - Weather source: `api.weather.gov`
  - Geocoding helper only: Open-Meteo Geocoding

- Resolve city/state to NWS grid point: **IMPLEMENTED**
  - `WeatherClient.resolve_location()`
  - `WeatherClient._nws_point()`

- Active alerts: **IMPLEMENTED**
  - `WeatherClient.fetch_alert_documents()`

- Detailed forecast narratives: **IMPLEMENTED**
  - `WeatherClient.fetch_forecast_documents()`

- Required normalized fields: **IMPLEMENTED**
  - stable `id`
  - `location`
  - `source_type`
  - `headline`
  - `narrative_text`
  - `issued_at`
  - `effective_at`
  - raw `payload JSONB`
  - `synced_at`

- `weather_documents` Lakebase table: **IMPLEMENTED**
  - DDL: `SCHEMA.md`
  - executable SQL: `sql/01_setup_weather.sql`
  - app migration: `lakebase.ensure_weather_schema()`

- psycopg2 + RealDictCursor connection pattern: **IMPLEMENTED**
  - `lakebase.py`

- `POST /weather/sync`: **IMPLEMENTED**
  - `app.py -> weather_sync()`

- Upsert/dedup on stable ID: **IMPLEMENTED (stretch)**
  - `ON CONFLICT (id) DO UPDATE`

## Part 2 — Vectorize / Embedding Pipeline

- Required standalone Python ingestion script: **IMPLEMENTED**
  - `notebooks/ingest_weather_embeddings.py`

- Read unembedded rows with psycopg2 helper: **IMPLEMENTED**

- Chunk long narrative text: **IMPLEMENTED**
  - chunk size = `800`
  - overlap = `100`

- Embedding model: **IMPLEMENTED**
  - `sentence-transformers/all-MiniLM-L6-v2`

- Embedding dimensionality: **IMPLEMENTED**
  - `384`
  - schema is `VECTOR(384)`

- `weather_embeddings` table: **IMPLEMENTED**
  - `document_id` foreign key
  - `chunk_index`
  - `chunk_text`
  - `embedding VECTOR(384)`
  - `model_name`
  - `created_at`

- psycopg2 batch write: **IMPLEMENTED**
  - `psycopg2.extras.execute_values`
  - explicit `%s::vector` cast

- Spark JDBC write: **NOT USED**, as required

- HNSW cosine index: **IMPLEMENTED**
  - `weather_embeddings_hnsw_idx`
  - `USING hnsw (embedding vector_cosine_ops)`

## Part 3 — Retrieve / REST API

- `POST /weather/search`: **IMPLEMENTED**
  - `app.py -> weather_search()`

- Same embedding model for query and ingestion: **IMPLEMENTED**

- Cosine search operator `<=>`: **IMPLEMENTED**

- Join embeddings to source documents: **IMPLEMENTED**

- Top-K JSON results: **IMPLEMENTED**
  - `location`
  - `source_type`
  - `headline`
  - `chunk_text`
  - `similarity`

- Missing/empty query handling: **IMPLEMENTED**

- `top_k` bounds clamped to 1–20: **IMPLEMENTED**

- Empty embeddings table handling: **IMPLEMENTED**

- Optional `source_type` retrieval filter: **IMPLEMENTED (stretch)**

## Additional quality / demo features

- Deployed frontend: **IMPLEMENTED**
  - `templates/index.html`
  - visually demonstrates sync → embed → search

- Live document/embedding statistics: **IMPLEMENTED**
  - `GET /weather/stats`

- Raw document inspection endpoint: **IMPLEMENTED**
  - `GET /weather/documents`

- Clean JSON exception handling: **IMPLEMENTED**

- OAuth/no hard-coded DB passwords: **IMPLEMENTED**
  - Databricks App service principal
  - short-lived database credential

## Submission artifacts

- GitHub repository URL: **INCLUDED**
  - https://github.com/PedroD1265/dataexpert-weather-vector-retrieval

- Databricks App URL: **INCLUDED**
  - https://dataexpert-weather-vector-app-7405607999696356.16.azure.databricksapps.com

- `README.md`: **INCLUDED**
- `README_WEATHER.md`: **INCLUDED**
- `SCHEMA.md` with readable DDL: **INCLUDED**
- source code ZIP: **TO EXPORT AFTER FINAL TEST**
- screenshots: **TO CAPTURE AFTER FINAL TEST**

## Evidence screenshots to include in final ZIP

1. `01_deployed_app.png`
   - Databricks App UI visible and running.

2. `02_weather_sync.png`
   - successful `/weather/sync` result with Chicago/Austin.

3. `03_weather_documents.png`
   - SQL result showing `weather_documents` sample rows and narrative text.

4. `04_weather_embeddings_384.png`
   - SQL result showing model name and `vector_dims(embedding) = 384`.

5. `05_semantic_search.png`
   - semantic query and ranked results with similarity values.

6. `06_hnsw_index.png`
   - `pg_indexes` result showing `weather_embeddings_hnsw_idx` and `vector_cosine_ops`.
