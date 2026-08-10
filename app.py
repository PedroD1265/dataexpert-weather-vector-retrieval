"""Weather Intelligence REST API + demo UI for the DataExpert Day 2 homework."""

import logging
import os

from flask import Flask, jsonify, render_template, request

import lakebase
from embedding_pipeline import (
    EMBEDDING_MODEL_NAME,
    embed_pending_documents,
    embed_query,
)
from weather_client import WeatherClient, WeatherClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather-vector-app")

app = Flask(__name__)

ALLOWED_SOURCE_TYPES = {"alert", "forecast"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/healthz")
def healthz():
    return jsonify({
        "status": "ok",
        "service": "weather-vector-retrieval",
        "embedding_model": EMBEDDING_MODEL_NAME,
    })


@app.errorhandler(Exception)
def handle_exception(err):
    logger.exception("Unhandled exception")
    status_code = getattr(err, "code", 500)
    if not isinstance(status_code, int):
        status_code = 500
    return jsonify({"error": str(err)}), status_code


@app.route("/weather/sync", methods=["POST"])
def weather_sync():
    """Harvest NWS alerts + forecast narratives and upsert into Lakebase.

    JSON body example:
        {"locations": ["Chicago, IL", "Austin, TX"], "limit": 50}
    """
    lakebase.ensure_weather_schema()

    body = request.get_json(silent=True) or {}
    locations = body.get("locations")

    if not isinstance(locations, list) or not locations:
        return jsonify({"error": "locations must be a non-empty JSON array of strings"}), 400

    cleaned_locations = [
        item.strip()
        for item in locations
        if isinstance(item, str) and item.strip()
    ]
    if not cleaned_locations:
        return jsonify({"error": "No valid locations were supplied"}), 400

    try:
        limit = int(body.get("limit", 50))
    except (TypeError, ValueError):
        return jsonify({"error": "limit must be an integer"}), 400
    limit = max(1, min(limit, 100))

    client = WeatherClient()
    all_documents = []
    per_location = []

    for location in cleaned_locations:
        try:
            documents = client.harvest_location(location, limit=limit)
            all_documents.extend(documents)
            per_location.append({
                "location": location,
                "documents": len(documents),
                "status": "ok",
            })
        except WeatherClientError as exc:
            per_location.append({
                "location": location,
                "documents": 0,
                "status": "error",
                "error": str(exc),
            })

    if not all_documents:
        return jsonify({
            "error": "No weather documents could be harvested",
            "locations": per_location,
        }), 502

    synced = lakebase.upsert_weather_documents(all_documents)
    return jsonify({
        "synced": synced,
        "documents_fetched": len(all_documents),
        "locations": per_location,
        "source": "National Weather Service API",
    })


@app.route("/weather/embed", methods=["POST"])
def weather_embed():
    """Embed previously synced weather documents into vector(384) rows.

    This endpoint is a convenient demo trigger. The same pipeline is also
    available as notebooks/ingest_weather_embeddings.py, as required by the
    assignment.
    """
    lakebase.ensure_weather_schema()
    body = request.get_json(silent=True) or {}

    limit = body.get("limit")
    if limit is not None:
        try:
            limit = max(1, min(int(limit), 1000))
        except (TypeError, ValueError):
            return jsonify({"error": "limit must be an integer"}), 400

    result = embed_pending_documents(limit=limit)
    return jsonify(result)


@app.route("/weather/search", methods=["POST"])
def weather_search():
    """Semantic cosine-similarity search over Lakebase pgvector embeddings.

    JSON body example:
        {"query": "risk of flooding near rivers", "top_k": 5}
    """
    lakebase.ensure_weather_schema()
    body = request.get_json(silent=True) or {}

    query = body.get("query", "")
    if not isinstance(query, str) or not query.strip():
        return jsonify({"error": "query is required and must be a non-empty string"}), 400
    query = query.strip()

    try:
        top_k = int(body.get("top_k", 5))
    except (TypeError, ValueError):
        return jsonify({"error": "top_k must be an integer"}), 400
    top_k = max(1, min(top_k, 20))

    source_type = body.get("source_type")
    if source_type is not None:
        if source_type not in ALLOWED_SOURCE_TYPES:
            return jsonify({
                "error": "source_type must be 'alert' or 'forecast'"
            }), 400

    embedding_count = lakebase.run_query(
        "SELECT COUNT(*) AS count FROM public.weather_embeddings"
    )[0]["count"]
    if embedding_count == 0:
        return jsonify({
            "query": query,
            "top_k": top_k,
            "results": [],
            "message": "weather_embeddings is empty. Run /weather/sync and /weather/embed first.",
        })

    query_vector = embed_query(query)

    params = [query_vector]
    where_sql = ""
    if source_type:
        where_sql = "WHERE d.source_type = %s"
        params.append(source_type)

    # The same query vector is passed again for ORDER BY, matching the
    # assignment's pgvector cosine-distance pattern.
    params.extend([query_vector, top_k])

    rows = lakebase.run_query(
        f"""
        SELECT
            d.id,
            d.location,
            d.source_type,
            d.headline,
            d.narrative_text,
            e.chunk_index,
            e.chunk_text,
            e.model_name,
            1 - (e.embedding <=> %s::vector) AS similarity
        FROM public.weather_embeddings e
        JOIN public.weather_documents d
          ON d.id = e.document_id
        {where_sql}
        ORDER BY e.embedding <=> %s::vector
        LIMIT %s
        """,
        tuple(params),
    )

    results = []
    for row in rows:
        row = dict(row)
        row["similarity"] = float(row["similarity"])
        results.append(row)

    return jsonify({
        "query": query,
        "top_k": top_k,
        "model": EMBEDDING_MODEL_NAME,
        "results": results,
    })


@app.route("/weather/documents", methods=["GET"])
def weather_documents():
    lakebase.ensure_weather_schema()
    try:
        limit = int(request.args.get("limit", 25))
    except ValueError:
        limit = 25
    limit = max(1, min(limit, 100))

    rows = lakebase.run_query(
        """
        SELECT id, location, source_type, headline, narrative_text,
               issued_at, effective_at, synced_at
        FROM public.weather_documents
        ORDER BY synced_at DESC, location, source_type
        LIMIT %s
        """,
        (limit,),
    )
    return jsonify(rows)


@app.route("/weather/stats", methods=["GET"])
def weather_stats():
    lakebase.ensure_weather_schema()

    totals = lakebase.run_query(
        """
        SELECT
            COUNT(*) AS documents,
            COUNT(*) FILTER (WHERE source_type = 'alert') AS alerts,
            COUNT(*) FILTER (WHERE source_type = 'forecast') AS forecasts
        FROM public.weather_documents
        """
    )[0]

    embeddings = lakebase.run_query(
        """
        SELECT COUNT(*) AS embeddings,
               COUNT(DISTINCT document_id) AS embedded_documents
        FROM public.weather_embeddings
        """
    )[0]

    return jsonify({**dict(totals), **dict(embeddings)})


if __name__ == "__main__":
    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("FLASK_RUN_PORT", "8000")))
    app.run(host=host, port=port, debug=False)
