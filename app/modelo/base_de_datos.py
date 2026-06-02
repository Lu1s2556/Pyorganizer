import sqlite3
import os
from datetime import datetime
from pathlib import Path


class BaseDeDatos:
    """Clase para manejar la base de dato SQLITE"""

    def __init__(self, nombre_db='organizador.db'):
        base_dir = Path(__file__).parent.parent / "recursos"
        base_dir.mkdir(parents=True, exist_ok=True)

        self.ruta_db = base_dir / nombre_db
        self.conexion = None
        self.cursor = None
        self.inicializar_db()

    def inicializar_db(self):
        try:
            self.conexion = sqlite3.connect(str(self.ruta_db))
            self.conexion.row_factory = sqlite3.Row
            self.cursor = self.conexion.cursor()
            print(f"✓ Conectado a: {self.ruta_db}")
        except sqlite3.Error as e:
            print(f"Error al inicializar la base de datos: {e}")
            raise

    def cerrar_conexion(self):
        if self.conexion:
            self.conexion.close()

    def confirmar(self):
        if self.conexion:
            self.conexion.commit()

    def revertir(self):
        if self.conexion:
            self.conexion.rollback()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.revertir()
        self.cerrar_conexion()
        return False


class GestorBaseDatos:
    """Gestor completo de la base de datos de Pyorganizer"""

    def __init__(self, db_name="organizador.db"):
        self.db = BaseDeDatos(nombre_db=db_name)

    def crear_tablas(self):
        """Crea todas las tablas del sistema"""

        # Tabla historial_operaciones
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_operaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_archivo TEXT NOT NULL,
                extension TEXT,
                ruta_origen TEXT NOT NULL,
                ruta_destino TEXT NOT NULL,
                tipo_operacion TEXT NOT NULL CHECK(tipo_operacion IN ('crear', 'mover', 'borrar', 'copiar')),
                tamano_bytes INTEGER DEFAULT 0,
                fecha_operacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                usuario TEXT DEFAULT 'sistema',
                estado TEXT DEFAULT 'completado' CHECK(estado IN ('completado', 'fallido', 'cancelado'))
            )
        """)

        # Tabla carpetas_monitoreadas
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS carpetas_monitoreadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ruta TEXT NOT NULL UNIQUE,
                nombre_alias TEXT,
                activa BOOLEAN DEFAULT 1,
                fecha_agregada DATETIME DEFAULT CURRENT_TIMESTAMP,
                ultima_operacion DATETIME
            )
        """)

        # Tabla configuraciones
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuraciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clave TEXT NOT NULL UNIQUE,
                valor TEXT,
                tipo_dato TEXT DEFAULT 'texto',
                descripcion TEXT,
                fecha_modificacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla reglas_organizacion
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reglas_organizacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                extension TEXT,
                carpeta_destino TEXT NOT NULL,
                prioridad INTEGER DEFAULT 0,
                activa BOOLEAN DEFAULT 1,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla directorios_destino (carpetas designadas por reglas u usuario)
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS directorios_destino (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ruta TEXT NOT NULL UNIQUE,
                nombre_alias TEXT,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Tabla errores_log
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS errores_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_error TEXT NOT NULL,
                mensaje TEXT,
                traceback TEXT,
                fecha_ocurrido DATETIME DEFAULT CURRENT_TIMESTAMP,
                resuelta BOOLEAN DEFAULT 0
            )
        """)

        # Tabla sesiones
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sesiones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inicio_sesion DATETIME DEFAULT CURRENT_TIMESTAMP,
                fin_sesion DATETIME,
                operaciones_realizadas INTEGER DEFAULT 0,
                archivos_procesados INTEGER DEFAULT 0
            )
        """)

        # Índices
        self.db.cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_fecha ON historial_operaciones(fecha_operacion)")
        self.db.cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_tipo ON historial_operaciones(tipo_operacion)")
        self.db.cursor.execute("CREATE INDEX IF NOT EXISTS idx_errores_fecha ON errores_log(fecha_ocurrido)")

        self.db.confirmar()
        print("✓ Tablas creadas exitosamente")
        # Después de crear tablas, sembrar datos por defecto si están vacías
        try:
            self.sembrar_si_vacia()
        except Exception as e:
            print(f"Error durante el seeding por defecto: {e}")

    def registrar_operacion(self, nombre_archivo, extension, ruta_origen, ruta_destino, tipo_operacion, tamano_bytes=0, usuario='sistema', estado='completado'):
        try:
            self.db.cursor.execute("""
                INSERT INTO historial_operaciones (nombre_archivo, extension, ruta_origen, ruta_destino, tipo_operacion, tamano_bytes, usuario, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nombre_archivo, extension, ruta_origen, ruta_destino, tipo_operacion, tamano_bytes, usuario, estado))
            self.db.confirmar()
            return True
        except sqlite3.Error as e:
            self.logar_error("registro_operacion", str(e))
            return False

    def obtener_historial(self, limite=50, tipo_operacion=None):
        try:
            if tipo_operacion:
                self.db.cursor.execute("""
                    SELECT * FROM historial_operaciones 
                    WHERE tipo_operacion = ? 
                    ORDER BY fecha_operacion DESC 
                    LIMIT ?
                """, (tipo_operacion, limite))
            else:
                self.db.cursor.execute("""
                    SELECT * FROM historial_operaciones 
                    ORDER BY fecha_operacion DESC 
                    LIMIT ?
                """, (limite,))
            return self.db.cursor.fetchall()
        except sqlite3.Error as e:
            self.logar_error("obtener_historial", str(e))
            return self.db.cursor.fetchall()

    def buscar_en_historial(self, termino_busqueda):
        try:
            self.db.cursor.execute("""
                SELECT * FROM historial_operaciones 
                WHERE nombre_archivo LIKE ? OR ruta_origen LIKE ? OR ruta_destino LIKE ?
                ORDER BY fecha_operacion DESC
            """, (f"%{termino_busqueda}%", f"%{termino_busqueda}%", f"%{termino_busqueda}%"))
            return self.db.cursor.fetchall()
        except sqlite3.Error as e:
            self.logar_error("buscar_en_historial", str(e))
            return self.db.cursor.fetchall()

    def obtener_estadisticas(self):
        stats = {}
        self.db.cursor.execute("SELECT COUNT(*) AS total FROM historial_operaciones")
        stats['total_operaciones'] = self.db.cursor.fetchone()[0]
        self.db.cursor.execute("""SELECT tipo_operacion, COUNT(*) AS cantidad FROM historial_operaciones GROUP BY tipo_operacion""")
        stats['por_tipo'] = {row['tipo_operacion']: row['cantidad'] for row in self.db.cursor.fetchall()}
        self.db.cursor.execute("SELECT SUM(tamano_bytes) AS total_bytes FROM historial_operaciones")
        stats['total_bytes'] = self.db.cursor.fetchone()['total_bytes'] or 0
        self.db.cursor.execute("""SELECT COUNT(*) AS total FROM historial_operaciones WHERE DATE(fecha_operacion) = DATE('now')""")
        stats['operaciones_hoy'] = self.db.cursor.fetchone()['total']
        return stats

    def guardar_configuracion(self, clave, valor, tipo_dato='texto', descripcion=None):
        try:
            self.db.cursor.execute("""
                INSERT OR REPLACE INTO configuraciones (clave, valor, tipo_dato, descripcion) 
                VALUES (?, ?, ?, ?)
            """, (clave, valor, tipo_dato, descripcion))
            self.db.confirmar()
            return True
        except sqlite3.Error as e:
            self.logar_error("guardar_configuracion", str(e))
            return False

    def obtener_configuracion(self, clave, valor_default=None):
        self.db.cursor.execute("SELECT valor FROM configuraciones WHERE clave = ?", (clave,))
        resultado = self.db.cursor.fetchone()
        return resultado['valor'] if resultado else valor_default

    def inicializar_configuraciones_default(self):
        config = [
            ("tema", "Fusion", "texto", "Tema visual de la aplicación"),
            ("idioma", "es", "texto", "Idioma de la interfaz"),
            ("umbral_confianza_ia", "0.2", "numero", "Umbral de confianza para la IA"),
            ("monitoreo_activo", "true", "booleano", "Monitoreo de carpetas activo"),
            ("ruta_default_descargas", "", "texto", "Ruta predeterminada de descargas"),
            ("ruta_default_escritorio", "", "texto", "Ruta predeterminada del escritorio"),
            ("crear_backup_auto", "true", "booleano", "Crear backup automático"),
            ("max_operaciones_undo", "10", "numero", "Máximo de operaciones para deshacer"),
        ]
        for clave, valor, tipo, desc in config:
            existe = self.obtener_configuracion(clave)
            if existe is None:
                self.guardar_configuracion(clave, valor, tipo, desc)
        print("✓ Configuraciones inicializadas")

    def sembrar_si_vacia(self):
        """Inserta datos por defecto si las tablas clave están vacías."""
        # Verificar directorios origen (carpetas_monitoreadas)
        self.db.cursor.execute("SELECT COUNT(*) AS cnt FROM carpetas_monitoreadas")
        cnt_origen = self.db.cursor.fetchone()[0]

        # Verificar directorios destino
        self.db.cursor.execute("SELECT COUNT(*) AS cnt FROM directorios_destino")
        cnt_destino = self.db.cursor.fetchone()[0]

        # Verificar reglas
        self.db.cursor.execute("SELECT COUNT(*) AS cnt FROM reglas_organizacion")
        cnt_reglas = self.db.cursor.fetchone()[0]

        if cnt_origen == 0:
            usuario = os.path.expanduser("~")
            defaults_origen = [
                (f"{usuario}/Downloads", "descargas"),
                (f"{usuario}/Desktop", "escritorio"),
                (f"{usuario}/Documents", "documentos"),
            ]
            for ruta, alias in defaults_origen:
                try:
                    self.agregar_carpeta_monitoreada(ruta, alias)
                except Exception:
                    pass

        if cnt_destino == 0:
            defaults_destino = [
                (os.path.join(os.path.expanduser("~"), "Imágenes"), "Imágenes"),
                (os.path.join(os.path.expanduser("~"), "Documentos"), "Documentos"),
                (os.path.join(os.path.expanduser("~"), "Programas"), "Programas"),
            ]
            for ruta, alias in defaults_destino:
                try:
                    self.db.cursor.execute(
                        "INSERT OR IGNORE INTO directorios_destino (ruta, nombre_alias) VALUES (?, ?)",
                        (ruta, alias)
                    )
                except sqlite3.Error as e:
                    self.logar_error("seed_directorios_destino", str(e))
            self.db.confirmar()

        if cnt_reglas == 0:
            # Asegurar que existen destinos para asociar
            self.db.cursor.execute("SELECT id, ruta, nombre_alias FROM directorios_destino")
            destinos = {row['nombre_alias']: row['ruta'] for row in self.db.cursor.fetchall()}

            reglas_default = [
                ("Documentos", ".pdf,.docx,.txt", destinos.get('Documentos', 'Documentos'), 10),
                ("Imágenes", ".jpg,.png", destinos.get('Imágenes', 'Imágenes'), 10),
                ("Ejecutables", ".exe,.msi", destinos.get('Programas', 'Programas'), 5),
            ]
            for nombre, ext, destino, prioridad in reglas_default:
                try:
                    self.agregar_regla(nombre, ext, destino, prioridad)
                except Exception:
                    pass

        # Commit final por si dejó operaciones pendientes
        self.db.confirmar()

    def agregar_regla(self, nombre, extension, carpeta_destino, prioridad=0, activa=True):
        try:
            self.db.cursor.execute("""
                INSERT INTO reglas_organizacion (nombre, extension, carpeta_destino, prioridad, activa) 
                VALUES (?, ?, ?, ?, ?)
            """, (nombre, extension, carpeta_destino, prioridad, int(activa)))
            self.db.confirmar()
            return True
        except sqlite3.Error as e:
            self.logar_error("agregar_regla_organizacion", str(e))
            return False

    def obtener_reglas(self, solo_activas=True):
        try:
            if solo_activas:
                self.db.cursor.execute("SELECT * FROM reglas_organizacion WHERE activa = 1 ORDER BY prioridad DESC")
            else:
                self.db.cursor.execute("SELECT * FROM reglas_organizacion ORDER BY prioridad DESC")
            return self.db.cursor.fetchall()
        except sqlite3.Error as e:
            self.logar_error("obtener_reglas_organizacion", str(e))
            return self.db.cursor.fetchall()

    def agregar_carpeta_monitoreada(self, ruta, nombre_alias=None):
        try:
            self.db.cursor.execute("""
                INSERT OR IGNORE INTO carpetas_monitoreadas (ruta, nombre_alias, activa) 
                VALUES (?, ?, 1)
            """, (ruta, nombre_alias))
            self.db.confirmar()
            return True
        except sqlite3.Error as e:
            self.logar_error("agregar_carpeta_monitoreada", str(e))
            return False

    def obtener_carpetas_monitoreadas(self):
        self.db.cursor.execute("SELECT * FROM carpetas_monitoreadas WHERE activa = 1")
        return self.db.cursor.fetchall()

    def logar_error(self, tipo_error, mensaje, traceback=None):
        try:
            self.db.cursor.execute("""
                INSERT INTO errores_log (tipo_error, mensaje, traceback, fecha_ocurrido) 
                VALUES (?, ?, ?, ?)
            """, (tipo_error, mensaje, traceback, datetime.now()))
            self.db.confirmar()
            return True
        except sqlite3.Error as e:
            print(f"Error al logar error en la base de datos: {e}")
            return False

    def obtener_errores(self, solo_no_resueltos=True):
        try:
            if solo_no_resueltos:
                self.db.cursor.execute("SELECT * FROM errores_log WHERE resuelta = 0 ORDER BY fecha_ocurrido DESC")
            else:
                self.db.cursor.execute("SELECT * FROM errores_log ORDER BY fecha_ocurrido DESC")
            return self.db.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener errores: {e}")
            return self.db.cursor.fetchall()

    def iniciar_sesion(self):
        self.db.cursor.execute("INSERT INTO sesiones (inicio_sesion) VALUES (?)", (datetime.now(),))
        self.db.confirmar()
        return self.db.cursor.lastrowid

    def cerrar_sesion(self, id_sesion, operaciones=0, archivos=0):
        self.db.cursor.execute("""
            UPDATE sesiones 
            SET fin_sesion = ?, operaciones_realizadas = ?, archivos_procesados = ?
            WHERE id = ?
        """, (datetime.now(), operaciones, archivos, id_sesion))
        self.db.confirmar()

    def verificar_integridad(self):
        self.db.cursor.execute("PRAGMA integrity_check")
        resultado = self.db.cursor.fetchone()
        return resultado[0] == 'ok'

    def obtener_tamano_db(self):
        # CORREGIDO: self.db.ruta_db
        return self.db.ruta_db.stat().st_size if self.db.ruta_db.exists() else 0

    def cerrar(self):
        self.db.cerrar_conexion()


def inicializar_nueva_db():
    """Inicializa una nueva base de datos desde cero"""
    print("=" * 50)
    print("INICIALIZANDO NUEVA BASE DE DATOS")
    print("=" * 50)

    # Crear gestor
    gestor = GestorBaseDatos("organizador.db")

    # Crear tablas
    gestor.crear_tablas()

    # Inicializar configuraciones
    gestor.inicializar_configuraciones_default()

    # Agregar carpetas por defecto
    usuario = os.path.expanduser("~")
    gestor.agregar_carpeta_monitoreada(f"{usuario}/Downloads", "descargas")
    gestor.agregar_carpeta_monitoreada(f"{usuario}/Desktop", "escritorio")
    gestor.agregar_carpeta_monitoreada(f"{usuario}/Documents", "documentos")

    # Agregar reglas por defecto
    reglas_default = [
        ("Imágenes", ".jpg,.png,.gif,.bmp,.webp", "Imágenes", 10),
        ("Documentos", ".pdf,.doc,.docx,.txt,.xls,.xlsx", "Documentos", 10),
        ("Videos", ".mp4,.avi,.mkv,.mov,.wmv", "Videos", 10),
        ("Audio", ".mp3,.wav,.flac,.aac,.ogg", "Audio", 10),
        ("Comprimidos", ".zip,.rar,.7z,.tar,.gz", "Comprimidos", 5),
        ("Ejecutables", ".exe,.msi,.bat,.sh", "Programas", 5),
    ]

    for nombre, ext, destino, prioridad in reglas_default:
        gestor.agregar_regla(nombre, ext, destino, prioridad)

    # Verificar integridad
    if gestor.verificar_integridad():
        print(" Integridad de la base de datos verificada")
    else:
        print(" Advertencia: Problemas de integridad detectados")

    # Mostrar tamaño
    tamano = gestor.obtener_tamano_db()
    print(f" Tamaño de la base de datos: {tamano} bytes")

    gestor.cerrar()

    print("=" * 50)
    print("BASE DE DATOS CREADA EXITOSAMENTE")
    print("=" * 50)

    return True


if __name__ == "__main__":
    inicializar_nueva_db()
