"""
Script de diagnóstico y limpieza de la base de datos.
Elimina reglas huérfanas (sin directorio destino correspondiente).
"""
import sqlite3
from pathlib import Path

db_path = Path('app/recursos/organizador.db')
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 60)
print("ESTADO ANTES DE LA LIMPIEZA")
print("=" * 60)

# Directorios destino
c.execute("SELECT * FROM directorios_destino")
destinos = c.fetchall()
print(f"\nDIRECTORIOS_DESTINO ({len(destinos)}):")
alias_validos = set()
for d in destinos:
    print(f"  id={d['id']} alias='{d['nombre_alias']}' ruta='{d['ruta']}'")
    if d['nombre_alias']:
        alias_validos.add(d['nombre_alias'].lower().strip())

print(f"\nAlias válidos: {alias_validos}")

# Reglas
c.execute("SELECT * FROM reglas_organizacion ORDER BY id")
reglas = c.fetchall()
print(f"\nREGLAS_ORGANIZACION ({len(reglas)}):")
reglas_huerfanas = []
for r in reglas:
    alias = r['carpeta_destino'].lower().strip() if r['carpeta_destino'] else ''
    es_huerfana = alias not in alias_validos
    estado = "⚠️ HUÉRFANA" if es_huerfana else "✅ OK"
    print(f"  id={r['id']} nombre='{r['nombre']}' destino='{r['carpeta_destino']}' {estado}")
    if es_huerfana:
        reglas_huerfanas.append(r['id'])

print(f"\n{'='*60}")
print(f"Reglas huérfanas a eliminar: {reglas_huerfanas}")

if reglas_huerfanas:
    resp = input("\n¿Eliminar reglas huérfanas? (s/n): ").strip().lower()
    if resp == 's':
        for rid in reglas_huerfanas:
            c.execute("DELETE FROM reglas_organizacion WHERE id = ?", (rid,))
            c.execute("DELETE FROM regla_extensiones WHERE regla_id = ?", (rid,))
        conn.commit()
        print("✅ Reglas huérfanas eliminadas.")
    else:
        print("Sin cambios.")
else:
    print("✅ No hay reglas huérfanas.")

# Estado final
print("\n" + "=" * 60)
print("ESTADO FINAL")
print("=" * 60)
c.execute("SELECT * FROM reglas_organizacion ORDER BY id")
reglas = c.fetchall()
print(f"\nREGLAS_ORGANIZACION ({len(reglas)}):")
for r in reglas:
    print(f"  id={r['id']} nombre='{r['nombre']}' ext='{r['extension']}' destino='{r['carpeta_destino']}' activa={r['activa']}")

conn.close()
print("\nListo.")
