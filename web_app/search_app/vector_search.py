"""
Semantic (vector) search over the Article collection, backed by ChromaDB and a
Hugging Face sentence-embedding model.

This module is intentionally kept separate from the Flask views / Mongo models
so that:
  - it can be unit tested without spinning up Flask or Mongo,
  - the embedding model and the ChromaDB client are created once per process
    and reused (loading a transformer model is the expensive part, so we
    never want to do it per-request),
  - it is the single place that knows how "relevant" is defined.

Environment variables (all optional, sensible defaults for docker-compose):
  CHROMADB_HOST            default: "localhost"
  CHROMADB_PORT            default: 8000
  EMBEDDING_MODEL           default: "sentence-transformers/all-MiniLM-L6-v2"
  SEARCH_DISTANCE_THRESHOLD default: 0.75  (cosine distance, lower = closer)
  SEARCH_MAX_RESULTS        default: 25    (safety cap, NOT the relevance cutoff)
"""

import os

import chromadb
from chromadb.utils import embedding_functions

COLLECTION_NAME = "articles"

CHROMA_HOST = os.environ.get("CHROMADB_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMADB_PORT", 8000))

# all-MiniLM-L6-v2 is a small (~80MB), fast sentence-transformer model that
# still gives good semantic search quality - a good fit for the "lightweight
# and efficient" requirement. Swappable via env var without code changes.
EMBEDDING_MODEL_NAME = os.environ.get(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

# Chroma's cosine distance is 1 - cosine_similarity, so it ranges [0, 2] and
# 0 means "identical". 0.75 is a conservative default (~ roughly >= 0.25
# cosine similarity) that favors precision; tune per-dataset via env var.
DEFAULT_DISTANCE_THRESHOLD = float(os.environ.get("SEARCH_DISTANCE_THRESHOLD", 0.75))
DEFAULT_MAX_RESULTS = int(os.environ.get("SEARCH_MAX_RESULTS", 25))

_client = None
_collection = None
_embedding_function = None


def get_client():
    """Lazily create (and cache) the ChromaDB HTTP client."""
    global _client
    if _client is None:
        _client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    return _client


def get_embedding_function():
    """Lazily create (and cache) the Hugging Face embedding function.

    This is the expensive line (it loads the model weights), so it must only
    ever run once per process, not once per request.
    """
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )
    return _embedding_function


def get_collection():
    """Lazily create (and cache) the Chroma collection handle."""
    global _collection
    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=get_embedding_function(),
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def reset_collection():
    """Drop and recreate the collection. Used by `flask load-news` so that
    re-running the load command doesn't leave stale/duplicate vectors around.
    """
    global _collection
    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        # Collection didn't exist yet - fine on a first run.
        pass
    _collection = None
    return get_collection()


def index_articles(ids, texts, batch_size=256):
    """Embed and upsert `texts` (with matching `ids`) into the collection.

    `ids` should be stable, unique identifiers - we use the Mongo document id
    (as a string) so that a vector search hit can be mapped straight back to
    its Article without a second lookup by text.
    """
    if len(ids) != len(texts):
        raise ValueError("ids and texts must be the same length")

    collection = get_collection()
    for start in range(0, len(texts), batch_size):
        batch_ids = ids[start : start + batch_size]
        batch_texts = texts[start : start + batch_size]
        collection.upsert(ids=batch_ids, documents=batch_texts)


def semantic_search(
    query,
    max_results=DEFAULT_MAX_RESULTS,
    distance_threshold=DEFAULT_DISTANCE_THRESHOLD,
):
    """Return the articles that are actually relevant to `query`.

    Unlike the old keyword search, this does NOT return a fixed number of
    results. `max_results` is only a safety cap on how many candidates we ask
    Chroma to rank; `distance_threshold` is what actually decides relevance -
    candidates past the threshold are dropped, so a very specific query can
    return 1 result and a broad one can return more, up to the cap.

    Returns a list of dicts: [{"id": ..., "text": ..., "distance": ...}, ...]
    ordered from most to least relevant.
    """
    if not query or not query.strip():
        return []

    collection = get_collection()
    available = collection.count()
    if available == 0:
        return []

    n_results = min(max_results, available)
    results = collection.query(query_texts=[query], n_results=n_results)

    ids = results["ids"][0]
    docs = results["documents"][0]
    distances = results["distances"][0]

    return [
        {"id": _id, "text": doc, "distance": dist}
        for _id, doc, dist in zip(ids, docs, distances)
        if dist <= distance_threshold
    ]
