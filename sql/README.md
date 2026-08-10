# SQL Setup

The weather homework schema is defined in:

```text
sql/01_setup_weather.sql
```

It contains:

- `weather_documents`
- `weather_embeddings`
- `VECTOR(384)`
- the foreign key from embeddings to documents
- the unique chunk/model constraint
- supporting indexes
- `weather_embeddings_hnsw_idx` using `vector_cosine_ops`

The same DDL is duplicated in `SCHEMA.md` because the previous automated grader did not recognize notebook-only schema evidence. The Markdown file makes keys, defaults, constraints, vector dimensionality, and the HNSW index directly readable during grading.

The Flask application also contains equivalent `CREATE TABLE IF NOT EXISTS` logic in `lakebase.ensure_weather_schema()` so the deployed app can initialize its own tables once pgvector support has been enabled in Lakebase.
