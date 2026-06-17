import os
import time
from pathlib import Path
from queue import Empty, Queue
from PySide6.QtCore import QObject, QMutex, QMutexLocker, QSemaphore, QThread, Signal
from app.utiles.watchdog_handler import WatchdogHandler
from app.utiles.file_waiter import wait_for_file_ready
from app.controlador.controlador_asistente import AsistenteVigiData
from app.core.motor_organizador import MotorOrganizadorCore
import weakref


class WatcherWorker(QObject):
    """Conecta el WatchdogHandler con la lógica de espera y movimiento.

    - El handler encola eventos de archivos en memoria.
    - Usa un set temporal para debouncing de rutas antes de procesarlas.
    - Inicia un QThread que consume la cola y emite signals a la UI.
    """

    file_ready = Signal(str)
    move_result = Signal(dict)

    def __init__(self, watch_root=None, parent=None):
        super().__init__(parent)
        self._db_path = None
        self._event_queue = Queue()
        self._queued_paths = set()
        self._queue_lock = QMutex()
        handler = WatchdogHandler(
            watch_root=watch_root,
            event_queue=self._event_queue,
            queued_paths=self._queued_paths,
            queue_lock=self._queue_lock,
        )
        self._handler_ref = weakref.ref(handler)
        
        self._worker_thread = None
        self._ensure_worker_thread()

    def _ensure_worker_thread(self):
        if self._worker_thread is None:
            self._worker_thread = WatcherWorkerThread(
                event_queue=self._event_queue,
                queued_paths=self._queued_paths,
                queue_lock=self._queue_lock,
            )
            self._worker_thread.file_ready.connect(self.file_ready)
            self._worker_thread.move_result.connect(self.move_result)    

    def set_db_path(self, db_path):
        self._db_path = db_path
        handler = self._handler_ref() if hasattr(self, '_handler_ref') else None
        if handler:
            handler.set_db_path(db_path)
        self._worker_thread.set_db_path(db_path)
        if not self._worker_thread.isRunning():
            self._worker_thread.start()

    def stop(self):
        self._worker_thread.stop()
        self._worker_thread.wait(1000)


class WatcherWorkerThread(QThread):
    file_ready = Signal(str)
    move_result = Signal(dict)

    def __init__(self, event_queue, queued_paths, queue_lock, parent=None):
        super().__init__(parent)
        self._event_queue = event_queue
        self._queued_paths = queued_paths
        self._queue_lock = queue_lock
        self._db_path = None
        self._core = None
        self._config_cache = None
        self._db_mtime = None
        self._move_semaphore = QSemaphore(3)
        self._stop_requested = False
        # No instanciamos AsistenteVigiData aquí; lo obtendremos desde MotorOrganizadorCore
        self._asistente_ref = None


    def set_db_path(self, db_path):
        self._db_path = db_path
        self._core = None
        # limpiar cache de configuración y actualizar mtime
        self._config_cache = None
        try:
            self._db_mtime = os.path.getmtime(self._db_path)
        except Exception:
            self._db_mtime = None
        # Cargar o recargar configuración si es necesario
        try:
            # comprobar mtime para recarga ligera
            try:
                current_mtime = os.path.getmtime(self._db_path) if self._db_path else None
            if event_tuple is None:
                current_mtime = None

            if self._config_cache is None or (self._db_mtime is not None and current_mtime is not None and current_mtime != self._db_mtime):
                # recargar configuración
                try:
                    self._core = MotorOrganizadorCore(self._db_path)
                    origenes, destinos, reglas = self._core.obtener_configuracion()
                    self._config_cache = (origenes, destinos, reglas)
                    self._db_mtime = current_mtime
                except Exception:
                    self._release_queued_path(path)
                    return
            else:
                origenes, destinos, reglas = self._config_cache
        except Exception:
            self._release_queued_path(path)
            return
                continue

            path, _event_type = event_tuple
            self._process_path(path)

    def _process_path(self, path: str):
    lower = path.lower()
    if lower.endswith('.crdownload') or lower.endswith('.part') or lower.endswith('.tmp'):
        self._release_queued_path(path)
        return

    ready = wait_for_file_ready(path, timeout=300, poll_interval=2.0)
    if not ready:
        self._release_queued_path(path)
        return

    self.file_ready.emit(path)

    if not self._db_path:
        self._release_queued_path(path)
        return

    try:
        # Usar MotorOrganizadorCore correctamente
        core = MotorOrganizadorCore(self._db_path)
        origenes, destinos, reglas = core.obtener_configuracion()
        
        # Procesar el archivo usando el método del core
        exito, mensaje = core.procesar_archivo(
            ruta_archivo=path,
            conexion_compartida=None,
            destinos=destinos,
            reglas=reglas,
            ruta_origen_defecto=os.path.dirname(path)
        )
        
        p = Path(path)
        if exito:
            try:
                self.move_result.emit({"path": str(p), "success": True, "message": mensaje})
            except Exception:
                pass
        else:
            try:
                self.move_result.emit({"path": str(p), "success": False, "message": mensaje or "No se aplicó ninguna regla"})
            except Exception:
                pass
                
    except Exception as e:
        try:
            self.move_result.emit({"path": str(path), "success": False, "message": str(e)})
        except Exception:
            pass
    finally:
        self._release_queued_path(path)
        time.sleep(0.1)
                
    def _release_queued_path(self, path: str):
        try:
            with QMutexLocker(self._queue_lock):
                self._queued_paths.discard(os.path.abspath(path))
        except Exception:
            pass
