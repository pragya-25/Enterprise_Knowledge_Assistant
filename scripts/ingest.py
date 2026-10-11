"""
Read data/raw/<department>/*.md -> chunk -> embed -> store in Qdrant.

Run from the project root:
    python -m scripts.ingest
"""
import uuid
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (Distance, VectorParams, PointStruct,
                                  PayloadSchemaType)
from app.core import config
from app.ingestion.chunker import chunk_markdown

BATCH = 64


def load_chunks():
    all_chunks = []
    for dept_dir in sorted(p for p in config.RAW_DIR.iterdir() if p.is_dir()):
        dept = dept_dir.name
        roles = config.DEPARTMENT_ACCESS.get(dept)
        if roles is None:
            print(f"[skip] unknown department folder: {dept}")
            continue
        for f in sorted(dept_dir.glob("*.md")):
            text = f.read_text(encoding="utf-8", errors="ignore")
            fallback = f.stem.split("__")[-1].replace("-", " ").title()
            for i, c in enumerate(chunk_markdown(text, fallback)):
                c.update(department=dept, allowed_roles=roles,
                         source=f.name, chunk_index=i)
                all_chunks.append(c)
        print(f"  loaded {dept}")
    return all_chunks


def main():
    print("1/4 Reading and chunking...")
    chunks = load_chunks()
    print(f"    {len(chunks)} chunks")

    print("2/4 Loading embedding model (first run downloads ~130 MB)...")
    model = SentenceTransformer(config.EMBEDDING_MODEL)

    print("3/4 Preparing Qdrant collection...")
    client = QdrantClient(url=config.QDRANT_URL)
    if client.collection_exists(config.COLLECTION):
        client.delete_collection(config.COLLECTION)
    client.create_collection(
        config.COLLECTION,
        vectors_config=VectorParams(size=config.EMBEDDING_DIM, distance=Distance.COSINE),
    )
    # indexes make the role/department filters fast
    for field in ("allowed_roles", "department"):
        client.create_payload_index(config.COLLECTION, field, PayloadSchemaType.KEYWORD)

    print("4/4 Embedding and uploading...")
    for start in range(0, len(chunks), BATCH):
        batch = chunks[start:start + BATCH]
        # embed title + section + text so the vector knows the context
        texts = [f"{c['title']} - {c['section']}\n{c['text']}" for c in batch]
        vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{c['source']}#{c['chunk_index']}")),
                vector=v.tolist(),
                payload=c,
            )
            for c, v in zip(batch, vectors)
        ]
        client.upsert(config.COLLECTION, points)
        print(f"    {min(start + BATCH, len(chunks))}/{len(chunks)}")

    print("Done.")


if __name__ == "__main__":
    main()
