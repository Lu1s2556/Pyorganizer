import os
import sqlite3
from pathlib import Path
from datetime import datetime

class ModeloOrganizador:
    def __init__(self):
        # Ruta de la base de datos local
        self.db_path = Path(__file__).resolve().parent.parent / 'recursos' / 'organizador.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.inicializar_base_de_datos()

    def inicializar_base_de_datos(self):
        """Crea la tabla de historial si no existe para garantizar la persistencia"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
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
        conn.commit()
        conn.close()

    def registrar_accion(self, nombre, tipo, origen, destino, tamano_bytes):
        """Guarda en SQLite los campos requeridos en el informe del proyecto"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tamano_mb = round(tamano_bytes / (1024 * 1024), 2) # Convertir a MB
            
            cursor.execute("""
                INSERT INTO historial (nombre, tipo, origen, destino, fecha, tamano)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nombre, tipo, origen, destino, fecha_actual, tamano_mb))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error al registrar en BD: {e}")

    def crear_carpeta(self, ruta_clave, nombre_carpeta):
        """Crea una carpeta físicamente en la ruta indicada por el usuario"""
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