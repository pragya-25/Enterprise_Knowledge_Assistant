import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS query_logs (
    id          SERIAL PRIMARY KEY,
    username    TEXT NOT NULL,
    role        TEXT NOT NULL,
    question    TEXT NOT NULL,
    found       BOOLEAN NOT NULL,
    top_score   DOUBLE PRECISION,
    latency_ms  INTEGER,
    created_at  TIMESTAMPTZ DEFAULT now()
);
"""


@contextmanager
def get_conn():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"),
                            cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(SCHEMA)
