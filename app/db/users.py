"""All SQL lives here, so the API code stays readable and easy to test."""
from app.db.database import get_conn


def get_user_by_username(username: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, username, password_hash, role FROM users WHERE username = %s",
                    (username,))
        return cur.fetchone()


def upsert_user(username: str, password_hash: str, role: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)
               ON CONFLICT (username) DO UPDATE
               SET password_hash = EXCLUDED.password_hash, role = EXCLUDED.role""",
            (username, password_hash, role))


def log_query(username, role, question, found, top_score, latency_ms):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO query_logs (username, role, question, found, top_score, latency_ms)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (username, role, question, found, top_score, latency_ms))


def recent_logs(limit: int = 50):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""SELECT username, role, question, found, top_score, latency_ms, created_at
                       FROM query_logs ORDER BY id DESC LIMIT %s""", (limit,))
        return cur.fetchall()
