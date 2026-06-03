import os
import time
import threading
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
from app.utiles.watchdog_handler import WatchdogHandler
from app.utiles.file_waiter import wait_for_file_ready
from app.controlador.controlador_asistente import AsistenteVigiData
from app.core.motor_organizador import MotorOrganizadorCore
print("DEBUG: Cargando controlador/watcher_worker.py...")


class WatcherWorker(QObject):
    """Conecta el WatchdogHandler con la lógica de espera (Fase 2).

    - Escucha `file_detected` y en un hilo separado espera hasta que el archivo esté libre.
    - No mueve archivos; emite `file_ready` cuando esté listo.
    """

    file_ready = Signal(str)
    move_result = Signal(dict)

    def __init__(self, watch_root=None, parent=None):
        super().__init__(parent)
        self.handler = WatchdogHandler(watch_root=watch_root)
        self.handler.file_detected.connect(self._on_file_detected)
        self._db_path = None
        # Limitar concurrencia de operaciones de movimiento para controlar memoria (baja: 1)
        self._move_semaphore = threading.BoundedSemaphore(value=1)
        self._core = None
        # Cola en disco para reintentos cuando hay saturación
        self._queue_path = Path(__file__).resolve().parent.parent / 'recursos' / 'watcher_queue.txt'
        self._queue_path.parent.mkdir(parents=True, exist_ok=True)
        self._queue_lock = threading.Lock()
        self._queue_processor_thread = threading.Thread(target=self._process_queue_loop, daemon=True)
        self._queue_processor_thread.start()

    def set_db_path(self, db_path):
        self._db_path = db_path
        # Cachear instancia del core para evitar recrearla por cada archivo
        try:
            self._core = MotorOrganizadorCore(self._db_path)
        except Exception:
            self._core = None

    @Slot(str)
    def _on_file_detected(self, path: str):
        t = threading.Thread(target=self._wait_and_emit, args=(path,), daemon=True)
        t.start()

    def _wait_and_emit(self, path: str):
        lower = path.lower()
        if lower.endswith('.crdownload') or lower.endswith('.part') or lower.endswith('.tmp'):
            try:
                print(f"[watcher_worker] ignoring temporary file: {path}")
            except Exception:
                pass
            return

        try:
            print(f"[watcher_worker] waiting for file ready: {path}")
        except Exception:
            pass

        ready = wait_for_file_ready(path, timeout=300, poll_interval=1.0)
        if ready:
            try:
                print(f"[watcher_worker] file ready: {path}")
            except Exception:
                pass
            self.file_ready.emit(path)
            try:
                if self._db_path:
                    core = self._core or MotorOrganizadorCore(self._db_path)
                    _, destinos, reglas = core.obtener_configuracion()

                    ext = os.path.splitext(path)[1].lower()
                    destino_alias = None
                    fallback_alias = None
                    for regla in reglas:
                        regla_ext = regla.get('extension')
                        if regla_ext and regla_ext.lower() == ext:
                            destino_alias = regla.get('destino_alias')
                            break
                        if regla_ext is None and fallback_alias is None:
                            fallback_alias = regla.get('destino_alias')

                    if destino_alias is None:
                        destino_alias = fallback_alias

                    if destino_alias and destino_alias in destinos:
                        destino_dir = destinos[destino_alias]
                        os.makedirs(destino_dir, exist_ok=True)
                        # Controlar número simultáneo de movimientos
                        acquired = self._move_semaphore.acquire(blocking=False)
                        if not acquired:
                            # Si está saturado, encolar la ruta en disco para procesarla luego
                            try:
                                with self._queue_lock:
                                    with open(self._queue_path, 'a', encoding='utf-8') as qf:
                                        qf.write(str(path) + "\n")
                                try:
                                    self.move_result.emit({"path": str(path), "success": False, "message": "Encolado por saturación"})
                                except Exception:
                                    pass
                            except Exception:
                                try:
                                    self.move_result.emit({"path": str(path), "success": False, "message": "Saturado: no se pudo encolar"})
                                except Exception:
                                    pass
                            return
                        else:
                            try:
                                asist = AsistenteVigiData()
                                from pathlib import Path
                                p = Path(path)
                                # Throttle: pequeña pausa antes de mover para reducir I/O burst
                                time.sleep(0.2)
                                moved = asist._move_and_register(p, destino_dir, p.parent)
                                if moved:
                                    self.move_result.emit({"path": str(p), "success": True, "message": f"Movido a {destino_dir}"})
                                else:
                                    self.move_result.emit({"path": str(p), "success": False, "message": "Error al mover"})
                            except Exception as e:
                                try:
                                    self.move_result.emit({"path": str(path), "success": False, "message": str(e)})
                                except Exception:
                                    pass
                            finally:
                                try:
                                    # Liberar semáforo
                                    self._move_semaphore.release()
                                except Exception:
                                    pass
                                try:
                                    # Intentar limpiar referencias pesadas y forzar GC
                                    if hasattr(self, '_core'):
                                        try:
                                            # if core exposes a close/free method, call it (best-effort)
                                            close = getattr(self._core, 'close', None)
                                            if callable(close):
                                                close()
                                        except Exception:
                                            pass
                                        # remove cached core to free memory
                                        self._core = None
                                    import gc
                                    gc.collect()
                                except Exception:
                                    pass
                                # cooldown entre movimientos para reducir uso de CPU/IO
                                time.sleep(0.5)

    def _process_queue_loop(self):
        """Loop que procesa la cola en disco de forma lenta y con baja concurrencia."""
        while True:
            try:
                # Leer y procesar una entrada a la vez
                line = None
                with self._queue_lock:
                    if self._queue_path.exists():
                        with open(self._queue_path, 'r', encoding='utf-8') as qf:
                            lines = [l.strip() for l in qf.readlines() if l.strip()]
                        if lines:
                            line = lines[0]
                            # reescribir el archivo sin la primera línea
                            with open(self._queue_path, 'w', encoding='utf-8') as qf:
                                qf.write('\n'.join(lines[1:]))

                if line:
                    # Intentar procesar la línea respetando semáforo
                    try:
                        acquired = self._move_semaphore.acquire(timeout=1)
                        if not acquired:
                            # si no se puede, volver a encolar al final
                            with self._queue_lock:
                                with open(self._queue_path, 'a', encoding='utf-8') as qf:
                                    qf.write(line + "\n")
                            time.sleep(5)
                            continue

                        try:
                            # reusar lógica: esperar y mover si aplica
                            ready = wait_for_file_ready(line, timeout=30, poll_interval=1.0)
                            if ready and self._db_path:
                                core = self._core or MotorOrganizadorCore(self._db_path)
                                _, destinos, reglas = core.obtener_configuracion()
                                ext = os.path.splitext(line)[1].lower()
                                destino_alias = None
                                fallback_alias = None
                                for regla in reglas:
                                    regla_ext = regla.get('extension')
                                    if regla_ext and regla_ext.lower() == ext:
                                        destino_alias = regla.get('destino_alias')
                                        break
                                    if regla_ext is None and fallback_alias is None:
                                        fallback_alias = regla.get('destino_alias')
                                if destino_alias is None:
                                    destino_alias = fallback_alias
                                if destino_alias and destino_alias in destinos:
                                    destino_dir = destinos[destino_alias]
                                    os.makedirs(destino_dir, exist_ok=True)
                                    asist = AsistenteVigiData()
                                    from pathlib import Path
                                    p = Path(line)
                                    time.sleep(0.2)
                                    moved = asist._move_and_register(p, destino_dir, p.parent)
                                    if moved:
                                        try:
                                            self.move_result.emit({"path": str(p), "success": True, "message": f"Movido (cola) a {destino_dir}"})
                                        except Exception:
                                            pass
                        finally:
                            try:
                                self._move_semaphore.release()
                            except Exception:
                                pass
                            try:
                                import gc
                                gc.collect()
                            except Exception:
                                pass
                    except Exception:
                        # si falla, esperar un poco antes de reintentar
                        time.sleep(5)
                else:
                    time.sleep(3)
            except Exception:
                time.sleep(5)
