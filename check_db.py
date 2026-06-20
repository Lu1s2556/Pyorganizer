import sqlite3
from pathlib import Path

db_path = Path('app/recursos/organizador.db')
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Listar tablas
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('TABLAS:', [r[0] for r in c.fetchall()])
print()

# Ver reglas_organizacion
try:
    c.execute('SELECT * FROM reglas_organizacion LIMIT 20')
    rows = c.fetchall()
    print(f'REGLAS_ORGANIZACION ({len(rows)} filas):')
    for r in rows:
        print(' ', dict(r))
except Exception as e:
    print('Error reglas_organizacion:', e)
print()

# Ver directorios_destino
try:
    c.execute('SELECT * FROM directorios_destino')
    rows = c.fetchall()
    print(f'DIRECTORIOS_DESTINO ({len(rows)} filas):')
    for r in rows:
        print(' ', dict(r))
except Exception as e:
    print('Error directorios_destino:', e)

# Ver PRAGMA de reglas_organizacion
print()
c.execute('PRAGMA table_info(reglas_organizacion)')
cols = c.fetchall()
print('COLUMNAS reglas_organizacion:', [r['name'] for r in cols])

# Ver regla_extensiones
print()
try:
    c.execute('SELECT * FROM regla_extensiones LIMIT 20')
    rows = c.fetchall()
    print(f'REGLA_EXTENSIONES ({len(rows)} filas):')
    for r in rows:
        print(' ', dict(r))
except Exception as e:
    print('Error regla_extensiones:', e)

conn.close()
