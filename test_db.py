"""
Script de prueba para la nueva base de datos
Pyorganizer - Test de Base de Datos
"""

import sys
import os

# Agregar la raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar desde tu archivo
from app.modelo.base_de_datos import GestorBaseDatos, inicializar_nueva_db


def probar_base_datos():
    print("\n" + "=" * 50)
    print("PRUEBA DE LA NUEVA BASE DE DATOS")
    print("=" * 50 + "\n")
    
    # 1. Inicializar nueva DB
    print("1. Creando nueva base de datos...")
    inicializar_nueva_db()
    
    # 2. Conectar y probar
    print("\n2. Conectando a la base de datos...")
    db = GestorBaseDatos("organizador.db")
    
    # 3. Registrar operaciones de prueba
    print("\n3. Registrando operaciones de prueba...")
    
    db.registrar_operacion(
        nombre_archivo="foto_vacaciones.jpg",
        extension=".jpg",
        ruta_origen="C:/Users/Lu1s/Downloads/foto_vacaciones.jpg",
        ruta_destino="C:/Users/Lu1s/Pictures/Vacaciones/foto_vacaciones.jpg",
        tipo_operacion="mover",
        tamano_bytes=2048000,
        usuario="Lu1s2556",
        estado="completado"
    )
    
    db.registrar_operacion(
        nombre_archivo="informe.pdf",
        extension=".pdf",
        ruta_origen="C:/Users/Lu1s/Desktop/informe.pdf",
        ruta_destino="C:/Users/Lu1s/Documents/Trabajo/informe.pdf",
        tipo_operacion="mover",
        tamano_bytes=512000,
        usuario="Lu1s2556",
        estado="completado"
    )
    
    db.registrar_operacion(
        nombre_archivo="CarpetaProyectos",
        extension=None,
        ruta_origen="",
        ruta_destino="C:/Users/Lu1s/Documents/Proyectos",
        tipo_operacion="crear",
        tamano_bytes=0,
        usuario="jose2099XD",
        estado="completado"
    )
    
    print("   ✓ 3 operaciones registradas")
    
    # 4. Obtener historial
    print("\n4. Obteniendo historial...")
    historial = [dict(h) for h in db.obtener_historial(limite=10)]
    print(f"   ✓ {len(historial)} operaciones en historial")
    for h in historial:
        print(f"      - {h['nombre_archivo']} ({h['tipo_operacion']})")
    
    # 5. Obtener estadísticas
    print("\n5. Obteniendo estadísticas...")
    stats = db.obtener_estadisticas()
    print(f"   ✓ Total operaciones: {stats['total_operaciones']}")
    print(f"   ✓ Operaciones hoy: {stats['operaciones_hoy']}")
    print(f"   ✓ Por tipo: {stats['por_tipo']}")
    print(f"   ✓ Total bytes movidos: {stats['total_bytes']}")
    
    # 6. Probar configuraciones
    print("\n6. Probando configuraciones...")
    tema = db.obtener_configuracion("tema")
    print(f"   ✓ Tema actual: {tema}")
    
    db.guardar_configuracion("mi_nueva_config", "valor_prueba", "texto", "Descripción de prueba")
    valor = db.obtener_configuracion("mi_nueva_config")
    print(f"   ✓ Nueva config guardada: {valor}")
    
    # 7. Probar reglas
    print("\n7. Obteniendo reglas de organización...")
    reglas = [dict(r) for r in db.obtener_reglas()]
    print(f"   ✓ {len(reglas)} reglas cargadas")
    for r in reglas:
        nombre = r.get('nombre') or f"regla_{r.get('id')}"
        extension = r.get('extension')
        carpeta = r.get('carpeta_destino')
        print(f"      - {nombre}: {extension} → {carpeta}")
    
    # 8. Probar carpetas monitoreadas
    print("\n8. Obteniendo carpetas monitoreadas...")
    carpetas = [dict(c) for c in db.obtener_carpetas_monitoreadas()]
    print(f"   ✓ {len(carpetas)} carpetas monitoreadas")
    for c in carpetas:
        nombre_alias = c.get('nombre_alias') or c.get('nombre') or ''
        ruta = c.get('ruta')
        print(f"      - {nombre_alias}: {ruta}")
    
    # 9. Verificar integridad
    print("\n9. Verificando integridad...")
    integridad = db.verificar_integridad()
    print(f"   ✓ Integridad: {'OK' if integridad else 'FALLIDA'}")
    
    # 10. Probar búsqueda en historial
    print("\n10. Probando búsqueda en historial...")
    resultados = [dict(r) for r in db.buscar_en_historial("foto")]
    print(f"   ✓ Búsqueda encontrada: {len(resultados)} resultados")
    
    # Cerrar
    db.cerrar()
    
    print("\n" + "=" * 50)
    print("✓ TODAS LAS PRUEBAS PASARON")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    try:
        probar_base_datos()
    except Exception as e:
        print(f"\n✗ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
