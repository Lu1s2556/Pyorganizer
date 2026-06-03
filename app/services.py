import sqlite3
from pathlib import Path
from typing import Optional

def _connect(db_path: Optional[str]):
    if not db_path:
        raise ValueError('db_path required')
    return sqlite3.connect(db_path)

def get_total_movidos(db_path: str) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM historico')
        row = cur.fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()

def get_total_reglas(db_path: str) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM reglas')
        row = cur.fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()
