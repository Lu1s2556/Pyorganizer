import os
import sqlite3
from pathlib import Path
from datetime import datetime
from app.modelo.base_de_datos import BaseDeDatos, GestorBaseDatos
class ModeloOrganizador:
    def __init__(self):
        # Ruta dinámica de la base de datos en la carpeta recursos
        self.db_path = Path(__file__).resolve().parent.parent / 'recursos' / 'organizador.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.inicializar_base_de_datos()

    def inicializar_base_de_datos(self):
        """Crea las tablas necesarias para la persistencia del sistema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Tabla de Historial de acciones (Auditoría del sistema)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                tipo TEXT,
                origen TEXT,
                destino TEXT,
                fecha TEXT,
                tamano REAL
            )
        """)
        
        # Tabla de Reglas dinámicas normativas por carpeta
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reglas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alias_carpeta TEXT UNIQUE,
                extensiones_permitidas TEXT,  -- Almacena ej: "pdf,docx"
                palabras_clave TEXT            -- Almacena ej: "tarea,unellez"
            )
        """)
        conn.commit()
        conn.close()

    def registrar_accion(self, nombre, tipo, origen, destino, tamano_bytes):
        """Guarda en la base de datos los campos requeridos para la auditoría"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tamano_mb = round(tamano_bytes / (1024 * 1024), 2) # Conversión a Megabytes
            
            cursor.execute("""
                INSERT INTO historial (nombre, tipo, origen, destino, fecha, tamano)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nombre, tipo, origen, destino, fecha_actual, tamano_mb))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Error al registrar en BD: {e}")

    def guardar_o_actualizar_regla(self, alias, extensiones, palabras):
        """Inserta o actualiza las restricciones de organización de una carpeta"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reglas (alias_carpeta, extensiones_permitidas, palabras_clave)
                VALUES (?, ?, ?)
                ON CONFLICT(alias_carpeta) DO UPDATE SET
                    extensiones_permitidas=excluded.extensiones_permitidas,
                    palabras_clave=excluded.palabras_clave
            """, (alias.lower().strip(), extensiones.lower().strip(), palabras.lower().strip()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"⚠️ Error al guardar regla en BD: {e}")
            return False

    def obtener_todas_las_reglas(self):
        """Recupera el diccionario estructurado de reglas desde la base de datos"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT alias_carpeta, extensiones_permitidas, palabras_clave FROM reglas")
            filas = cursor.fetchall()
            conn.close()
            
            reglas_dict = {}
            for fila in filas:
                reglas_dict[fila[0]] = {
                    "extensiones": [ext.strip() for ext in fila[1].split(",") if ext.strip()],
                    "palabras": [pal.strip() for pal in fila[2].split(",") if pal.strip()]
                }
            return reglas_dict
        except Exception as e:
            print(f"⚠️ Error al cargar reglas de BD: {e}")
            return {}

    def crear_carpeta(self, ruta_clave, nombre_carpeta):
        """Crea físicamente un directorio en base a los alias estándar del sistema"""
        try:
            mapa_rutas = {
                "escritorio": Path.home() / "Desktop",
                "documentos": Path.home() / "Documents",
                "descargas": Path.home() / "Downloads",
                "fotos": Path.home() / "Pictures"
            }
            ruta_base = mapa_rutas.get(ruta_clave.lower(), Path.home() / "Desktop")
            ruta_final = ruta_base / nombre_carpeta
            ruta_final.mkdir(parents=True, exist_ok=True)
            return f"✅ Carpeta '{nombre_carpeta}' creada con éxito en {ruta_base.name}."
        except Exception as e:
            return f"❌ Error al crear carpeta: {str(e)}"