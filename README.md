# Weather Intelligence — Lakebase Vector Search

DataExpert.io **Rise of the AI Data Engineer — Day 2 Homework**.

This project implements the complete pipeline required by the **Vector Weather Retrieval Service** assignment:

**unstructured weather text → Lakebase → chunking → 384-dim embeddings → pgvector/HNSW → semantic REST retrieval**.

## Links

- GitHub repository: https://github.com/PedroD1265/dataexpert-weather-vector-retrieval
- Databricks App: https://dataexpert-weather-vector-app-7405607999696356.16.azure.databricksapps.com

## Architecture

```text
User / REST client
        |
        v
Databricks App (Flask)
        |
        +---- POST /weather/sync
        |          |
        |          +--> Open-Meteo Geocoding (location resolution only)
        |          +--> National Weather Service API
        |          +--> weather_documents (Lakebase)
        |
        +---- POST /weather/embed
        |          |
        |          +--> chunk size 800 / overlap 100
        |          +--> sentence-transformers/all-MiniLM-L6-v2
        |          +--> weather_embeddings VECTOR(384)
        |
        +---- POST /weather/search
                   |
                   +--> query embedding with the SAME model
                   +--> pgvector cosine distance <=>
                   +--> HNSW vector_cosine_ops index
                   +--> top-K semantic results
```

## Data source

The weather content source is the **U.S. National Weather Service API (`api.weather.gov`)** because it is free, requires no API key, and provides rich narrative text in active alerts and detailed forecasts.

**Open-Meteo Geocoding is used only to convert a city/state string such as `Chicago, IL` into latitude/longitude. It is not used as the weather content source.**

## Required endpoints

### `POST /weather/sync`

Harvest alerts and forecasts, normalize them, and upsert them into `public.weather_documents`.

```json
{
  "locations": ["Chicago, IL", "Austin, TX"],
  "limit": 50
}
```

Example response shape:

```json
{
  "synced": 28,
  "documents_fetched": 28,
  "source": "National Weather Service API",
  "locations": [
    {"location": "Chicago, IL", "documents": 14, "status": "ok"}
  ]
}
```

### `POST /weather/search`

Embed the query with the same MiniLM model and perform cosine similarity search using pgvector's `<=>` operator.

```json
{
  "query": "risk of flooding near rivers",
  "top_k": 5
}
```

Each result includes `location`, `source_type`, `headline`, `chunk_text`, and `similarity`.

### Additional demo endpoint: `POST /weather/embed`

Runs the same psycopg2 embedding pipeline as the required ingestion script. It is included to make the deployed demo easy to verify from the Databricks App UI.

The required standalone script is also provided at:

```text
notebooks/ingest_weather_embeddings.py
```

### Additional evidence endpoints

- `GET /weather/stats`
- `GET /weather/documents?limit=25`
- `GET /healthz`

## Lakebase schema

The full DDL is included in both:

- `SCHEMA.md` — plain Markdown so an automated grader can read the constraints directly.
- `sql/01_setup_weather.sql` — executable PostgreSQL DDL.

### `weather_documents`

Stores normalized raw weather documents and provenance:

- `id` — stable text primary key used for deduplication
- `location`
- `source_type` — `alert` or `forecast`
- `headline`
- `narrative_text` — unstructured text that is embedded
- `issued_at`
- `effective_at`
- `payload JSONB` — original API payload for provenance
- `synced_at`

### `weather_embeddings`

Stores chunk-level vectors:

- identity primary key
- `document_id` foreign key → `weather_documents.id`
- `chunk_index`
- `chunk_text`
- `embedding VECTOR(384)`
- `model_name`
- `created_at`
- unique constraint on `(document_id, chunk_index, model_name)`

The vector index is:

```sql
CREATE INDEX weather_embeddings_hnsw_idx
ON public.weather_embeddings
USING hnsw (embedding vector_cosine_ops);
```

## Chunking and embeddings

- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Dimensions: `384`
- Chunk size: `800` characters
- Chunk overlap: `100` characters
- Embeddings are normalized before insertion.

A sliding window is used so long NWS narratives can create multiple overlapping chunks. Short narratives normally remain a single chunk.

## psycopg2 write path

The assignment specifically requires `psycopg2`, not Spark JDBC, for the Lakebase write path.

This project uses:

```python
from psycopg2.extras import execute_values
```

and writes vectors with an explicit pgvector cast:

```sql
%s::vector
```

The ingestion script is `notebooks/ingest_weather_embeddings.py` and the same implementation pattern is shared by the Flask application in `embedding_pipeline.py`.

## Lakebase authentication

No passwords, API keys, or database credentials are committed to the repository.

The Databricks App Database Resource injects:

- `PGHOST`
- `PGPORT`
- `PGDATABASE`
- `PGUSER`
- `PGSSLMODE`

`lakebase.py` then calls the Databricks SDK to generate a **short-lived OAuth database credential** for each new psycopg2 connection using `ENDPOINT_NAME`.

## Run end-to-end

1. Enable Lakebase Search / pgvector support in the Lakebase project.
2. Add the Lakebase database as a Databricks App Database Resource.
3. Deploy this repository as the source for `dataexpert-weather-vector-app`.
4. Open the app UI.
5. Run **Step 1 — Sync** for `Chicago, IL` and `Austin, TX`.
6. Run **Step 2 — Embed**.
7. Run **Step 3 — Search** with a semantic query such as `risk of flooding near rivers`.
8. Refresh the UI and verify document/embedding counts persist in Lakebase.

## Validation and edge cases

Implemented:

- empty/malformed `locations` validation
- invalid location handling
- upstream API failure returned as a clean error
- stable IDs + `ON CONFLICT` upsert deduplication
- missing/empty search query → HTTP 400
- malformed `top_k` → HTTP 400
- `top_k` clamped to `1–20`
- optional `source_type` filter (`alert` or `forecast`)
- empty embeddings table returns a helpful response rather than a stack trace
- app-wide JSON error handling

## Main files

```text
app.py                              Flask UI + REST endpoints
weather_client.py                   Geocoding + NWS client and normalization
lakebase.py                         psycopg2 OAuth connection + DDL + upserts
embedding_pipeline.py               chunking + MiniLM + vector batch writes
notebooks/ingest_weather_embeddings.py  required psycopg2 ingestion script
sql/01_setup_weather.sql            executable DDL
SCHEMA.md                           grader-friendly schema evidence
README_WEATHER.md                   assignment-specific design notes
SUBMISSION_CHECKLIST.md             requirement-to-evidence mapping
SUBMISSION.md                       URLs and submission summary
templates/index.html                deployed demo frontend
```

## Known limitations / future improvements

- NWS weather data covers the United States, so weather ingestion is intentionally U.S.-focused.
- Forecast narratives are updated by the source and stable IDs upsert the current text for a forecast period.
- The demo uses a single embedding model; a production service would version embeddings more formally before model migration.
- The HNSW index is included for retrieval performance, but a larger corpus would be needed for a meaningful latency benchmark.
- A scheduled Databricks Job to refresh active alerts periodically would be a natural next step.

## Submission evidence

Recommended screenshots for the ZIP:

```text
evidence/
├── 01_deployed_app.png
├── 02_weather_sync.png
├── 03_weather_documents.png
├── 04_weather_embeddings_384.png
├── 05_semantic_search.png
└── 06_hnsw_index.png
```

See `SUBMISSION_CHECKLIST.md` for the exact proof each screenshot should contain.
