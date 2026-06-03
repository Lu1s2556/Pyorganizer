import os
import shutil
import sqlite3
from pathlib import Path

try:
    from PySide6.QtCore import QThread, Signal
except Exception:
    # If PySide6 isn't available in this environment, define fallbacks for linting/tests
    class QThread:
        def __init__(self):
            pass
    class Signal:
        def __init__(self, *args, **kwargs):
            pass

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.controlador.controlador_asistente import AsistenteVigiData


class WatchdogThread(QThread):
    """Hilo Qt que ejecuta un Observer de watchdog y emite señales cuando se crean archivos."""
    file_created = Signal(str)

    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self._observer = None
        self._running = False

    def run(self):
        # Cargar rutas origen desde la base de datos
        origenes = []
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT ruta FROM carpetas_monitoreadas WHERE activa = 1")
            origenes = [row[0] for row in cursor.fetchall()]
            conn.close()
        except Exception:
            origenes = []

        if not origenes:
            return

        event_handler = _CreatedHandler(self.file_created)
        self._observer = Observer()
        for ruta in origenes:
            if os.path.exists(ruta):
                try:
                    self._observer.schedule(event_handler, ruta, recursive=False)
                except Exception:
                    pass

        self._observer.start()
        self._running = True
        try:
            while self._running:
                self.msleep(200)
        finally:
            try:
                self._observer.stop()
                self._observer.join()
            except Exception:
                pass

    def stop(self):
        self._running = False


class _CreatedHandler(FileSystemEventHandler):
    def __init__(self, qt_signal):
        super().__init__()
        self.qt_signal = qt_signal

    def on_created(self, event):
        # Solo archivos
        if event.is_directory:
            return
        try:
            path = event.src_path
            # Emitir la ruta del archivo creado
            try:
                self.qt_signal.emit(path)
            except Exception:
                # si Signal no es real (entorno de pruebas), intentar llamar como función
                try:
                    self.qt_signal(path)
                except Exception:
                    pass
        except Exception:
            pass


class MotorOrganizadorCore:
    def __init__(self, db_path):
        self.db_path = db_path

    def _conectar_db(self):
        return sqlite3.connect(str(self.db_path))

    def obtener_configuracion(self):
        """
        Extrae los orígenes, destinos y reglas organizadas por prioridad.
        Retorna estructuras de datos nativas (listas/dict) muy ligeras en memoria.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 1. Obtener carpetas de origen (monitoreadas)
        cursor.execute("SELECT ruta FROM carpetas_monitoreadas WHERE activa = 1")
        origenes = [Path(fila[0]) for fila in cursor.fetchall() if os.path.exists(fila[0])]

        # 2. Obtener mapas de carpetas destino (alias -> ruta_real)
        destinos = {}
        try:
            cursor.execute("SELECT nombre_alias, ruta FROM directorios_destino")
            destinos = {fila[0].lower(): Path(fila[1]) for fila in cursor.fetchall()}
        except Exception:
            # Fallbacks: try common alternative column names
            try:
                cursor.execute("SELECT alias, ruta FROM directorios_destino")
                destinos = {fila[0].lower(): Path(fila[1]) for fila in cursor.fetchall()}
            except Exception:
                try:
                    cursor.execute("SELECT nombre, ruta FROM directorios_destino")
                    destinos = {fila[0].lower(): Path(fila[1]) for fila in cursor.fetchall()}
                except Exception:
                    # As a last resort, attempt to read only ruta and create numeric aliases
                    try:
                        cursor.execute("SELECT ruta FROM directorios_destino")
                        for idx, fila in enumerate(cursor.fetchall()):
                            destinos[f"destino_{idx}"] = Path(fila[0])
                    except Exception:
                        destinos = {}

        # 3. Obtener reglas de organización activas ordenadas por prioridad de mayor a menor
        cursor.execute("""
            SELECT extension, carpeta_destino 
            FROM reglas_organizacion 
            WHERE activa = 1 
            ORDER BY fecha_creacion DESC
        """)
        reglas = []
        for fila in cursor.fetchall():
            ext = fila[0].strip().lower() if fila[0] else None
            reglas.append({
                "extension": ext,
                "destino_alias": fila[1].lower(),
            })

        conn.close()
        return origenes, destinos, reglas

    def procesar_organizacion(self, callback_progreso=None):
        """
        Escanea los directorios de origen y mueve los archivos basándose en las reglas.
        Usa un generador liviano para no saturar la memoria RAM.
        """
        origenes, destinos, reglas = self.obtener_configuracion()
        archivos_movidos = 0

        if not origenes or not destinos:
            return 0

        for ruta_origen in origenes:
            # Iterar solo sobre los archivos directos del origen (evitamos recursividad masiva para cuidar la RAM)
            try:
                for entrada in os.scandir(ruta_origen):
                    if entrada.is_file():
                        archivo_path = Path(entrada.path)
                        ext_archivo = archivo_path.suffix.lower().replace(".", "")

                        # Buscar qué regla coincide (al estar ordenadas por prioridad, la primera que aplique gana)
                        for regla in reglas:
                            coincide_ext = (regla["extension"] == ext_archivo) or (regla["extension"] is None)
                            alias_dest = regla["destino_alias"]

                            if coincide_ext and alias_dest in destinos:
                                ruta_final_dir = destinos[alias_dest]
                                
                                # Asegurar que la carpeta de destino exista físicamente
                                os.makedirs(ruta_final_dir, exist_ok=True)
                                
                                ruta_final_archivo = ruta_final_dir / archivo_path.name

                                # Manejo de colisiones de nombres (si el archivo ya existe en el destino)
                                if ruta_final_archivo.exists():
                                    nombre_base = archivo_path.stem
                                    contador = 1
                                    while ruta_final_archivo.exists():
                                        ruta_final_archivo = ruta_final_dir / f"{nombre_base}_{contador}.{ext_archivo}"
                                        contador += 1

                                try:
                                            # Delegate actual move + registration to helper in controller
                                            asist = AsistenteVigiData()
                                            # Ensure destino dir exists
                                            os.makedirs(ruta_final_dir, exist_ok=True)
                                            moved = asist._move_and_register(archivo_path, ruta_final_dir, ruta_origen)
                                            if moved:
                                                archivos_movidos += 1
                                                if callback_progreso:
                                                    callback_progreso(f"Movido: {archivo_path.name} → {alias_dest}")
                                except Exception as e:
                                    if callback_progreso:
                                        callback_progreso(f"Error al mover {archivo_path.name}: {str(e)}")
                                
                                break # Rompe el ciclo de reglas, pasa al siguiente archivo
            except Exception as e:
                if callback_progreso:
                    callback_progreso(f"Error accediendo a {ruta_origen}: {str(e)}")

        return archivos_movidos

    def escanear_ahora(self, callback_progreso=None):
        """Ejecuta un escaneo inmediato usando la lógica de organización.
        Retorna la cantidad de archivos movidos.
        """
        return self.procesar_organizacion(callback_progreso=callback_progreso)