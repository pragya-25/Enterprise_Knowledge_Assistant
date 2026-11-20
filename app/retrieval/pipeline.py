"""
Three retrieval modes, so we can measure what each step adds:

  vector : embeddings only                       (what we have today)
  hybrid : vector + BM25 keyword, merged with Reciprocal Rank Fusion
  rerank : hybrid, then a cross-encoder re-scores the best candidates

Every mode respects the role filter. The role check happens before any
text can reach the LLM.
"""
import os
import re
from functools import lru_cache

import numpy as np

from app.core import config
from app.retrieval import search as vector_search

POOL = 30           # candidates taken from each retriever
RERANK_POOL = 20    # candidates the cross-encoder re-scores
RRF_K = 60
RERANK_MODEL = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

STOPWORDS = set("""a an and are as at be by do does for from how i in is it of on or
that the this to was what when where which who why with you your can we our my me""".split())


def tokenize(text: str):
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS]


def _key(chunk):
    return (chunk["source"], chunk["chunk_index"])


# ---------------- BM25 (keyword search) ----------------

@lru_cache(maxsize=1)
def _bm25_index():
    """Load every chunk from Qdrant once and build an in-memory BM25 index."""
    from rank_bm25 import BM25Okapi
    client = vector_search._client()
    docs, offset = [], None
    while True:
        points, offset = client.scroll(config.COLLECTION, limit=1000, offset=offset,
                                       with_payload=True, with_vectors=False)
        docs.extend(p.payload for p in points)
        if offset is None:
            break
    corpus = [tokenize(f"{d['title']} {d['section']} {d['text']}") for d in docs]
    return BM25Okapi(corpus), docs


@lru_cache(maxsize=16)
def _role_mask(role: str):
    _, docs = _bm25_index()
    return np.array([role in d["allowed_roles"] for d in docs])


def bm25_search(query: str, role: str, k: int = POOL):
    bm25, docs = _bm25_index()
    tokens = tokenize(query)
    if not tokens:
        return []
    scores = bm25.get_scores(tokens)
    scores = np.where(_role_mask(role), scores, -1.0)   # role filter
    top = np.argsort(scores)[::-1][:k]
    return [{"score": float(scores[i]), **docs[i]} for i in top if scores[i] > 0]


# ---------------- Fusion ----------------

def rrf(result_lists, k=RRF_K):
    """Reciprocal Rank Fusion: chunks ranked high by several retrievers win."""
    fused = {}
    for results in result_lists:
        for rank, chunk in enumerate(results, 1):
            entry = fused.setdefault(_key(chunk), {"chunk": chunk, "score": 0.0})
            entry["score"] += 1.0 / (k + rank)
    ordered = sorted(fused.values(), key=lambda e: e["score"], reverse=True)
    return [{**e["chunk"], "score": e["score"]} for e in ordered]


# ---------------- Reranker ----------------

@lru_cache(maxsize=1)
def _reranker():
    from sentence_transformers import CrossEncoder
    return CrossEncoder(RERANK_MODEL, max_length=512)


def rerank(query: str, chunks, k: int):
    if not chunks:
        return []
    pairs = [(query, f"{c['title']} - {c['section']}\n{c['text']}") for c in chunks]
    scores = _reranker().predict(pairs)
    order = np.argsort(scores)[::-1][:k]
    return [{**chunks[i], "score": float(scores[i])} for i in order]


# ---------------- Public entry point ----------------

def retrieve_mode(query: str, role: str, mode: str = "rerank", k: int = 5):
    if mode == "vector":
        return vector_search.retrieve(query, role, k)

    fused = rrf([vector_search.retrieve(query, role, POOL),
                 bm25_search(query, role, POOL)])
    if mode == "hybrid":
        return fused[:k]
    if mode == "rerank":
        return rerank(query, fused[:RERANK_POOL], k)
    raise ValueError(f"unknown mode: {mode}")
