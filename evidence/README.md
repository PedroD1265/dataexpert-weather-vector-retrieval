# Submission Evidence

After the deployed app passes the end-to-end test, place these screenshots in this directory before exporting the final ZIP:

1. `01_deployed_app.png` — deployed Weather Intelligence UI and Databricks App URL.
2. `02_weather_sync.png` — successful sync for Chicago, IL and Austin, TX with document counts.
3. `03_weather_documents.png` — Lakebase SQL result showing normalized alert/forecast documents and narrative text.
4. `04_weather_embeddings_384.png` — Lakebase SQL result showing MiniLM model and `vector_dims(embedding) = 384`.
5. `05_semantic_search.png` — query plus ranked semantic results with similarity values.
6. `06_hnsw_index.png` — `pg_indexes` evidence showing `weather_embeddings_hnsw_idx` and `vector_cosine_ops`.

These images are evidence only; no credentials or secret values should appear in screenshots.
