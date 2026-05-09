import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "")


@contextmanager
def get_conn():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
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
