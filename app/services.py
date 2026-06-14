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
        cur.execute('SELECT COUNT(*) FROM historial_operaciones')
        row = cur.fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()

def get_total_reglas(db_path: str) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        # Contar solo reglas activas
        cur.execute('SELECT COUNT(*) FROM reglas_organizacion WHERE activa = 1')
        row = cur.fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()

def obtener_archivos_por_tipo(db_path: str, limite: int = 10):
    """Devuelve la lista de tuplas (extension, cantidad) ordenadas por cantidad descendente."""
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT extension, COUNT(*) as cnt FROM historial_operaciones GROUP BY extension ORDER BY cnt DESC LIMIT ?", (limite,))
        return [(row[0] if row[0] is not None else 'sin_extension', row[1]) for row in cur.fetchall()]
    finally:
        conn.close()
