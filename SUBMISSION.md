# Day 2 Homework Submission — Vector Weather Retrieval Service

## Databricks App URL

https://dataexpert-weather-vector-app-7405607999696356.16.azure.databricksapps.com

## Source-code repository

https://github.com/PedroD1265/dataexpert-weather-vector-retrieval

## What is implemented

The project harvests unstructured alert and forecast narratives from the National Weather Service API, stores normalized source documents in Lakebase, chunks and embeds the narratives with `sentence-transformers/all-MiniLM-L6-v2` into `VECTOR(384)` rows, and exposes pgvector cosine-similarity retrieval through `POST /weather/search`.

Required REST endpoints:

- `POST /weather/sync`
- `POST /weather/search`

Additional demo/verification endpoints:

- `POST /weather/embed`
- `GET /weather/stats`
- `GET /weather/documents`
- `GET /healthz`

## Security

No database passwords, API keys, tokens, or secrets are committed. The Databricks App uses its service principal plus a short-lived Lakebase OAuth credential generated at runtime.

## Evidence to include in final ZIP

- `evidence/01_deployed_app.png`
- `evidence/02_weather_sync.png`
- `evidence/03_weather_documents.png`
- `evidence/04_weather_embeddings_384.png`
- `evidence/05_semantic_search.png`
- `evidence/06_hnsw_index.png`

See `SUBMISSION_CHECKLIST.md` for the requirement-to-evidence mapping.
