"""
Test retrieval only (no LLM yet).

    python -m scripts.search "what is the parental leave policy"
    python -m scripts.search "salary bands" --role engineer
"""
import argparse
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny
from app.core import config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--role", default=None, help="only search docs this role may read")
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    model = SentenceTransformer(config.EMBEDDING_MODEL)
    client = QdrantClient(url=config.QDRANT_URL)

    qvec = model.encode(config.QUERY_PREFIX + args.query, normalize_embeddings=True)

    flt = None
    if args.role:
        flt = Filter(must=[FieldCondition(key="allowed_roles", match=MatchAny(any=[args.role]))])

    res = client.query_points(config.COLLECTION, query=qvec.tolist(),
                              query_filter=flt, limit=args.k, with_payload=True)

    print(f"\nQuery: {args.query}   (role filter: {args.role})\n")
    for i, p in enumerate(res.points, 1):
        pl = p.payload
        print(f"[{i}] score={p.score:.3f}  dept={pl['department']}  {pl['source']}")
        print(f"    section: {pl['section']}")
        print(f"    {pl['text'][:250].replace(chr(10), ' ')}...\n")


if __name__ == "__main__":
    main()
