import os
import urllib.parse
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "")


@contextmanager
def get_conn():
    url = urllib.parse.urlparse(DATABASE_URL)
    import sys
    print(f"[DB] host={url.hostname} port={url.port} user={url.username} db={url.path}", file=sys.stderr, flush=True)
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port or 5432,
        database=url.path.lstrip("/"),
        user=url.username,
        password=url.password,
        sslmode="require",
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    from pathlib import Path
    schema = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(schema)


def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    query = query.replace("?", "%s")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def fetch_one(query: str, params: tuple = ()):
    query = query.replace("?", "%s")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
    return dict(row) if row else None


def execute(query: str, params: tuple = ()) -> int:
    query = query.replace("?", "%s")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query + " RETURNING id" if query.strip().upper().startswith("INSERT") else query, params)
            if query.strip().upper().startswith("INSERT"):
                row = cur.fetchone()
                return row["id"] if row else None
            return None
