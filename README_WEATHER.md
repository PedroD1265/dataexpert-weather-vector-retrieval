# Vector Weather Retrieval Service — Assignment Notes

## Data source

The project uses the **National Weather Service API** as the sole weather-content provider because it requires no API key and exposes rich unstructured narrative text in active alerts and multi-day forecasts.

`Open-Meteo Geocoding` is used only to resolve user-friendly location strings such as `Chicago, IL` into latitude/longitude coordinates before calling NWS. It is not used as a second weather source.

## Schema decisions

Raw normalized documents are stored in `public.weather_documents` with:

- stable `id`
- `location`
- `source_type` (`alert` or `forecast`)
- `headline`
- `narrative_text`
- `issued_at`
- `effective_at`
- raw `payload JSONB`
- `synced_at`

Embeddings are stored in `public.weather_embeddings` with:

- identity `id`
- foreign key `document_id`
- `chunk_index`
- `chunk_text`
- `embedding VECTOR(384)`
- `model_name`
- `created_at`

The table uses a unique constraint on `(document_id, chunk_index, model_name)` and an HNSW cosine index:

```sql
CREATE INDEX weather_embeddings_hnsw_idx
ON public.weather_embeddings
USING hnsw (embedding vector_cosine_ops);
```

Full DDL is available in `SCHEMA.md` and `sql/01_setup_weather.sql`.

## Chunking and embedding model

- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Output dimensions: `384`
- Chunk size: `800` characters
- Chunk overlap: `100` characters

Most NWS forecast periods are short enough to remain one chunk. Longer alert descriptions/instructions are split using the overlapping sliding-window strategy.

## End-to-end pipeline

1. `POST /weather/sync`
   - resolves each location
   - calls NWS `/points`, forecast, and active-alert endpoints
   - normalizes alert/forecast narratives
   - upserts them into `weather_documents`

2. `POST /weather/embed` or `notebooks/ingest_weather_embeddings.py`
   - reads unembedded rows through `psycopg2`
   - chunks `narrative_text`
   - embeds with MiniLM
   - batch writes with `psycopg2.extras.execute_values`
   - explicitly casts vectors with `%s::vector`

3. `POST /weather/search`
   - validates `query`
   - clamps `top_k` to 1–20
   - embeds the query with the same model
   - joins `weather_embeddings` to `weather_documents`
   - ranks with cosine distance using `<=>`
   - returns `location`, `headline`, `chunk_text`, and `similarity`

## Example requests

### Sync

```json
POST /weather/sync
{
  "locations": ["Chicago, IL", "Austin, TX"],
  "limit": 50
}
```

### Search

```json
POST /weather/search
{
  "query": "flash flood risk this weekend",
  "top_k": 5
}
```

## Known limitations / improvements

- NWS is U.S.-only, so the ingestion workflow intentionally targets U.S. locations.
- The current implementation refreshes/upserts forecast periods rather than retaining every historical revision.
- HNSW is included, but a larger corpus would be required for a meaningful indexed-vs-unindexed benchmark.
- A scheduled Databricks Job to re-sync active alerts every N minutes would be the next production-oriented improvement.
