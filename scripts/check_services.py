"""Verify that Qdrant, Postgres and Redis are reachable."""
import os
from dotenv import load_dotenv

load_dotenv()


def check_qdrant():
    from qdrant_client import QdrantClient
    c = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
    c.get_collections()


def check_postgres():
    import psycopg2
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    conn.cursor().execute("SELECT 1")
    conn.close()


def check_redis():
    import redis
    redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0")).ping()


for name, fn in [("Qdrant", check_qdrant), ("Postgres", check_postgres), ("Redis", check_redis)]:
    try:
        fn()
        print(f"[OK]   {name}")
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
