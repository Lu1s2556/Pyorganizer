import gc
import os
import shutil
import sqlite3
from pathlib import Path
import psutil
import weakref

try:
    from PySide6.QtCore import QThread, Signal
except Exception:
    
    class QThread:
        def __init__(self):
            from collections import deque
            self._cache_reglas = None
            self._historial_procesamiento = deque(maxlen=1000)  # Cache de últimos archivos procesados para evitar re-procesos inmediatos
            pass
    class Signal:
        def __init__(self, *args, **kwargs):
            pass

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.controlador.controlador_asistente import AsistenteVigiData


class HiloOrganizador(QThread):
    """
    QThread encargado de ejecutar las tareas de ordenamiento pesado en 
    segundo plano, evitando congelar la interfaz de usuario (UI).
    """
    progreso_senal = Signal(str)  # Envía logs en tiempo real a la vista
    finalizado_senal = Signal(int) # Envía el conteo total al terminar

    def __init__(self, motor_core):
        super().__init__()
        self.motor_core = motor_core

    def run(self):
        try:
            # Llama a la rutina unificada del motor usando la señal como callback
            total_movidos = self.motor_core.procesar_organizacion(
                callback_progreso=self.progreso_senal.emit
            )
            self.finalizado_senal.emit(total_movidos)
        except Exception as e:
            self.progreso_senal.emit(f"❌ Error crítico en HiloOrganizador: {e}")
            self.finalizado_senal.emit(0)


# =====================================================================
# COMPONENTES EXISTENTES: WATCHDOG (MONITOREO EN TIEMPO REAL)
# =====================================================================
class WatchdogThread(QThread):
    """Hilo Qt que ejecuta un Observer de watchdog y emite señales cuando se crean archivos."""
    file_created = Signal(str)

    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self._observer = None
        self._running = False

    def run(self):
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
        if event.is_directory:
            return
        try:
            path = event.src_path
            try:
                self.qt_signal.emit(path)
            except Exception:
                try:
                    self.qt_signal(path)
                except Exception:
                    pass
        except Exception:
            pass


# =====================================================================
# NÚCLEO OPTIMIZADO: CORE DEL MOTOR ORGANIZADOR
# =====================================================================
class MotorOrganizadorCore:
    def __init__(self, db_path):
        self.db_path = db_path
        # Mantener referencia débil al asistente para evitar ciclos de referencia
        self._asistente_ref = weakref.ref(AsistenteVigiData())

    @property
    def asistente(self):
        return self._asistente_ref() if hasattr(self, '_asistente_ref') else None

    def _conectar_db(self):
        return sqlite3.connect(str(self.db_path))

    def obtener_configuracion(self):
        """
        Punto 2 del Plan: Extrae de forma limpia los orígenes, destinos y reglas activas.
        Retorna estructuras de datos nativas muy ligeras en memoria.
        """
        conn = None
        try:
            conn = self._conectar_db()
            cursor = conn.cursor()

            # 1. Obtener carpetas de origen (monitoreadas)
            # Limitar resultados y usar índice implícito para evitar cargas grandes
            cursor.execute("""
                SELECT ruta 
                FROM carpetas_monitoreadas 
                WHERE activa = 1 
                LIMIT 50
            """)
            origenes = [Path(fila[0]) for fila in cursor.fetchall() if os.path.exists(fila[0])]

            # 2. Obtener mapas de carpetas destino (nombre_alias -> ruta) de forma estricta
            cursor.execute("SELECT nombre_alias, ruta FROM directorios_destino")
            destinos = {fila[0].lower().strip(): Path(fila[1]) for fila in cursor.fetchall()}

            # 3. Obtener reglas de organización activas por carpeta de destino filtrada (Fase 2)
            # 3. Obtener reglas de organización activas como generador (no cargar todo en memoria)
            # Se delega la lógica de iteración a `generar_reglas` para poder consumir reglas
            # perezosamente fuera de este método.
            reglas = self.generar_reglas(cursor)
        finally:
            if conn:
                conn.close()

        return origenes, destinos, reglas

    def generar_reglas(self, cursor):
        """Generador que produce reglas una por una desde el cursor de DB."""
        try:
            cursor.execute("""
                SELECT id, extension, palabras_clave, carpeta_destino, nombre 
                FROM reglas_organizacion 
                WHERE activa = 1 
                ORDER BY fecha_creacion DESC
            """)
        except Exception:
            return

        for fila in cursor.fetchall():
            rid = fila[0]
            legacy_ext = fila[1].strip().lower() if fila[1] else None
            raw_keywords = fila[2]
            exts = []
            keywords = []

            if legacy_ext:
                parts = [p.strip() for p in legacy_ext.split(',') if p.strip()]
                for p in parts:
                    p = f'.{p}' if not p.startswith('.') else p
                    if p not in exts:
                        exts.append(p)

            try:
                cursor.execute("SELECT extension FROM regla_extensiones WHERE regla_id = ?", (rid,))
                for r2 in cursor.fetchall():
                    v = r2[0].strip().lower()
                    if v and not v.startswith('.'):
                        v = f'.{v.lstrip('.')}'
                    if v and v not in exts:
                        exts.append(v)
            except Exception:
                pass

            if raw_keywords:
                for keyword in [k.strip().lower() for k in str(raw_keywords).split(',') if k.strip()]:
                    if keyword not in keywords:
                        keywords.append(keyword)

            yield {
                "id": rid,
                "extensions": exts if exts else None,
                "keywords": keywords if keywords else None,
                "destino_alias": fila[3].lower().strip(),
                "nombre_regla": fila[4]
            }

    def procesar_archivo(self, ruta_archivo, conexion_compartida, destinos, reglas, ruta_origen_defecto=None):
        """
        Punto 1 del Plan: Función independiente que evalúa las reglas dinámicas vinculadas 
        a la carpeta destino, resuelve colisiones de nombres y procesa el movimiento.
        """
        archivo_path = Path(ruta_archivo)
        if not archivo_path.is_file():
            return False, None

        # Usar el sufijo directo con punto nativo de Python (ej: ".pdf")
        ext_archivo = archivo_path.suffix.lower().strip()
        origen_padre = str(ruta_origen_defecto) if ruta_origen_defecto else str(archivo_path.parent)

        # Evaluar secuencialmente las reglas cargadas desde la base de datos
        destino_alias = None
        fallback_alias = None
        for regla in reglas:
            alias_dest = regla.get("destino_alias")
            if alias_dest not in destinos:
                continue

            regla_exts = regla.get("extensions") or []
            regla_keywords = regla.get("keywords") or []

            if not regla_exts and not regla_keywords:
                fallback_alias = alias_dest if fallback_alias is None else fallback_alias
                continue

            if self._evaluar_regla_para_archivo(ext_archivo, archivo_path.name.lower(), regla_exts, regla_keywords):
                destino_alias = alias_dest
                break

        if destino_alias is None:
            destino_alias = fallback_alias

        if destino_alias and destino_alias in destinos:
            ruta_final_dir = destinos[destino_alias]
            try:
                # Garantizar existencia física de la carpeta destino
                os.makedirs(ruta_final_dir, exist_ok=True)
                ruta_final_archivo = ruta_final_dir / archivo_path.name
                if len(ruta_final_archivo.name) > 255:
                    nombre_base = archivo_path.stem[:250]  # Truncar para evitar errores de sistema de archivos
                    ruta_final_archivo = ruta_final_dir / f"{nombre_base}{ext_archivo}"

                # Resolver colisiones de nombres si el archivo ya existe manteniendo la extensión intacta
                if ruta_final_archivo.exists():
                    nombre_base = archivo_path.stem
                    contador = 1
                    while ruta_final_archivo.exists():
                        ruta_final_archivo = ruta_final_dir / f"{nombre_base}_{contador}{ext_archivo}"
                        contador += 1

                # Reusar el asistente cargado por el motor para evitar instancias repetidas
                moved = self.asistente._move_and_register(archivo_path, ruta_final_dir, origen_padre)

                if moved:
                    return True, f"✅ Organizado: {archivo_path.name} ➔ {destino_alias.upper()}"
            except Exception as e:
                return False, f"❌ Error al aplicar regla en {archivo_path.name}: {str(e)}"

        return False, None

    @staticmethod
    def _evaluar_regla_para_archivo(self, ext_archivo, nombre_archivo, regla_exts, regla_keywords):
        """Evalúa si la regla aplica según extensión, palabras clave o ambas."""
        tiene_ext = bool(regla_exts)
        tiene_keywords = bool(regla_keywords)

        if tiene_ext and tiene_keywords:
            return ext_archivo in regla_exts and any(keyword in nombre_archivo for keyword in regla_keywords)
        if tiene_ext:
            return ext_archivo in regla_exts
        if tiene_keywords:
            return any(keyword in nombre_archivo for keyword in regla_keywords)
        return False

    def procesar_organizacion(self, callback_progreso=None):
        
        origenes, destinos, reglas = self.obtener_configuracion()
        archivos_procesados = 0
        max_archivos = 1000  # Límite de archivos a procesar por ejecución para evitar sobrecarga

        if not origenes or not destinos:
            if callback_progreso:
                callback_progreso("⚠️ No hay carpetas de origen o destino activas en la configuración.")
            return 0

        # Apertura de una conexión persistente única para optimizar operaciones I/O
        conn = self._conectar_db()

        for ruta_origen in origenes:
            # Monitoreo de memoria antes de procesar cada origen
            try:
                memoria_mb = self._monitorear_memoria()
                if memoria_mb and memoria_mb > 500:
                    gc.collect()
                    if callback_progreso:
                        callback_progreso(f"👀 [Monitor] Memoria alta ({memoria_mb:.1f} MB). Forzando GC.")
            except Exception:
                pass
            try:
                # Iteración optimizada en bajo consumo usando os.scandir (Punto 4 del Plan)
                with os.scandir(ruta_origen) as it:
                    for entrada in it:
                        if entrada.is_file():
                            exito, mensaje = self.procesar_archivo(
                                ruta_archivo=entrada.path,
                                conexion_compartida=conn,
                                destinos=destinos,
                                reglas=reglas,
                                ruta_origen_defecto=ruta_origen
                            )
                            if exito:
                                archivos_procesados += 1
                                if callback_progreso and mensaje:
                                    callback_progreso(mensaje)
            except PermissionError:
                if callback_progreso:
                    callback_progreso(f"Permiso denegado para acceder a {ruta_origen.name}")                       
            except Exception as e:
                if callback_progreso:
                    callback_progreso(f"Error accediendo a {ruta_origen.name}: {str(e)}")

        conn.close()
        resultado = archivos_procesados
        import gc
        gc.collect()
        if callback_progreso:
            callback_progreso(f"✅ Organización finalizada. Total archivos procesados: {resultado}")
        return resultado

    def _monitorear_memoria(self):
        try:
            proceso = psutil.Process(os.getpid())
            memoria = proceso.memory_info().rss / 1024 / 1024  # MB
            return memoria
        except Exception:
            return None

    def escanear_ahora(self, callback_progreso=None):
        """
        Punto 2 del Plan: Método público y reutilizable. 
        Ejecuta un escaneo inmediato mapeando la lógica estructurada de organización.
        """
        return self.procesar_organizacion(callback_progreso=callback_progreso)