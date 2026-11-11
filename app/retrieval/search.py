"""Role-filtered vector search. One place that every part of the app calls."""
from functools import lru_cache
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny
from app.core import config


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(config.EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def _client():
    return QdrantClient(url=config.QDRANT_URL)


def retrieve(query: str, role: str, k: int = config.CANDIDATES_K):
    """Return the top-k chunks this role is allowed to see: [{score, ...payload}]."""
    qvec = _model().encode(config.QUERY_PREFIX + query, normalize_embeddings=True)
    # The security filter runs INSIDE Qdrant, before any text reaches the LLM.
    role_filter = Filter(must=[FieldCondition(key="allowed_roles", match=MatchAny(any=[role]))])
    res = _client().query_points(config.COLLECTION, query=qvec.tolist(),
                                 query_filter=role_filter, limit=k, with_payload=True)
    return [{"score": p.score, **p.payload} for p in res.points]
