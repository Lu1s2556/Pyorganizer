import os
import time
from pathlib import Path
from queue import Empty, Queue
from PySide6.QtCore import QObject, QMutex, QMutexLocker, QSemaphore, QThread, Signal
from app.utiles.watchdog_handler import WatchdogHandler
from app.utiles.file_waiter import wait_for_file_ready
from app.controlador.controlador_asistente import AsistenteVigiData
from app.core.motor_organizador import MotorOrganizadorCore


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
        self.handler = WatchdogHandler(
            watch_root=watch_root,
            event_queue=self._event_queue,
            queued_paths=self._queued_paths,
            queue_lock=self._queue_lock,
        )
        self._worker_thread = WatcherWorkerThread(
            event_queue=self._event_queue,
            queued_paths=self._queued_paths,
            queue_lock=self._queue_lock,
            parent=self,
        )
        self._worker_thread.file_ready.connect(self.file_ready)
        self._worker_thread.move_result.connect(self.move_result)
        self._worker_thread.start()

    def set_db_path(self, db_path):
        self._db_path = db_path
        self.handler.set_db_path(db_path)
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
        self._move_semaphore = QSemaphore(3)
        self._stop_requested = False
        self._asistente = AsistenteVigiData()


    def set_db_path(self, db_path):
        self._db_path = db_path
        if not self._core:
            self._core = MotorOrganizadorCore(self._db_path)
        core = self._core


    def stop(self):
        self._stop_requested = True

    def run(self):
        while not self._stop_requested:
            try:
                event_tuple = self._event_queue.get(timeout=1)
            except Empty:
                continue

            if event_tuple is None:
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
           if not self._core:
                self._core = MotorOrganizadorCore(self._db_path)
            core = self._core
            origenes, destinos, reglas = core._cargar_configuracion()
        except Exception:
            self._release_queued_path(path)
            return

        ext = os.path.splitext(path)[1].lower()
        destino_alias = None
        fallback_alias = None

        for regla in reglas:
            regla_ext = regla.get('extension')
            if regla_ext:
                lista_extensiones_permitidas = [e.strip().lstrip('.') for e in str(regla_ext).split(',') if e.strip()]
                if ext.lstrip('.') in lista_extensiones_permitidas:
                    destino_alias = regla.get('destino_alias')
                    break
            elif regla_ext is None and fallback_alias is None:
                fallback_alias = regla.get('destino_alias')

        if destino_alias is None:
            destino_alias = fallback_alias

        if not destino_alias or destino_alias not in destinos:
            self._release_queued_path(path)
            return

        destino_dir = destinos[destino_alias]
        os.makedirs(destino_dir, exist_ok=True)

        if not self._move_semaphore.tryAcquire(1):
            self._release_queued_path(path)
            try:
                self.move_result.emit({"path": str(path), "success": False, "message": "Saturado: no disponible para mover"})
            except Exception:
                pass
            return

        try:
            asist = self._asistente
            p = Path(path)
            time.sleep(0.2)
            moved = False
            attempts = 3
            for attempt in range(1, attempts + 1):
                try:
                    moved = asist._move_and_register(p, destino_dir, p.parent)
                    if moved:
                        break
                except FileNotFoundError:
                    moved = False
                except Exception:
                    moved = False
                time.sleep(0.3 * attempt)

            if moved:
                try:
                    self.move_result.emit({"path": str(p), "success": True, "message": f"Movido a {destino_dir}"})
                except Exception:
                    pass
            else:
                try:
                    self.move_result.emit({"path": str(p), "success": False, "message": "Error al mover"})
                except Exception:
                    pass
        except Exception as e:
            try:
                self.move_result.emit({"path": str(path), "success": False, "message": str(e)})
            except Exception:
                pass
        finally:
            self._move_semaphore.release()
            try:
                if hasattr(self, '_core'):
                    close = getattr(self._core, 'close', None)
                    if callable(close):
                        try:
                            close()
                        except Exception:
                            pass
                    self._core = None
            except Exception:
                pass
                        self._release_queued_path(path)
            time.sleep(0.5)

    def _release_queued_path(self, path: str):
        try:
            with QMutexLocker(self._queue_lock):
                self._queued_paths.discard(os.path.abspath(path))
        except Exception:
            pass
