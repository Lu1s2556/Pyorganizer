import os
import time
import threading
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
from app.utiles.watchdog_handler import WatchdogHandler
from app.utiles.file_waiter import wait_for_file_ready
from app.controlador.controlador_asistente import AsistenteVigiData
from app.core.motor_organizador import MotorOrganizadorCore


class WatcherWorker(QObject):
    """Conecta el WatchdogHandler con la lógica de espera y movimiento.

    - Escucha `file_detected` y en un hilo separado espera hasta que el archivo esté libre.
    - Si el sistema está saturado, encola en disco para reintentos posteriores.
    """

    file_ready = Signal(str)
    move_result = Signal(dict)

    def __init__(self, watch_root=None, parent=None):
        super().__init__(parent)
        self.handler = WatchdogHandler(watch_root=watch_root)
        self.handler.file_detected.connect(self._on_file_detected)
        self._db_path = None
        self._move_semaphore = threading.BoundedSemaphore(value=1)
        self._core = None
        self._queue_path = Path(__file__).resolve().parent.parent / 'recursos' / 'watcher_queue.txt'
        self._queue_path.parent.mkdir(parents=True, exist_ok=True)
        self._queue_lock = threading.Lock()
        self._queue_processor_thread = threading.Thread(target=self._process_queue_loop, daemon=True)
        self._queue_processor_thread.start()

    def set_db_path(self, db_path):
        self._db_path = db_path
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
        if not ready:
            return

        try:
            print(f"[watcher_worker] file ready: {path}")
        except Exception:
            pass

        # Emitimos siempre que esté listo
        try:
            self.file_ready.emit(path)
        except Exception:
            pass

        # Lógica de movimiento (si se configuró DB)
        if not self._db_path:
            return

        try:
            core = self._core or MotorOrganizadorCore(self._db_path)
            _, destinos, reglas = core.obtener_configuracion()
        except Exception:
            return

        ext = os.path.splitext(path)[1].lower()
        destino_alias = None
        fallback_alias = None

        for regla in reglas:
            regla_ext = regla.get('extension')
            if regla_ext:
                # regla_ext puede ser 'png,jpg,jpeg' o valores legacy con punto
                lista_extensiones_permitidas = [e.strip().lstrip('.') for e in str(regla_ext).split(',') if e.strip()]
                if ext.lstrip('.') in lista_extensiones_permitidas:
                    destino_alias = regla.get('destino_alias')
                    break
            elif regla_ext is None and fallback_alias is None:
                fallback_alias = regla.get('destino_alias')

        if destino_alias is None:
            destino_alias = fallback_alias

        if not destino_alias or destino_alias not in destinos:
            return

        destino_dir = destinos[destino_alias]
        os.makedirs(destino_dir, exist_ok=True)

        # Intentar adquirir semáforo para mover ahora; si falla, encolar en disco
        acquired = self._move_semaphore.acquire(blocking=False)
        if not acquired:
            try:
                with self._queue_lock:
                    with open(self._queue_path, 'a', encoding='utf-8') as qf:
                        qf.write(str(path) + '\n')
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

        # Si se adquirió semáforo, mover y liberar
        try:
            asist = AsistenteVigiData()
            from pathlib import Path as _P
            p = _P(path)
            time.sleep(0.2)
            # Intentar mover con reintentos para mitigar errores transitorios (WinError 2)
            moved = False
            attempts = 3
            for attempt in range(1, attempts + 1):
                try:
                    moved = asist._move_and_register(p, destino_dir, p.parent)
                    if moved:
                        break
                except FileNotFoundError:
                    moved = False
                except Exception as e:
                    moved = False
                # Backoff corto entre intentos
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
            try:
                self._move_semaphore.release()
            except Exception:
                pass
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
            try:
                import gc
                gc.collect()
            except Exception:
                pass
            time.sleep(0.5)

    def _process_queue_loop(self):
        """Procesa la cola en disco de rutas pendientes."""
        while True:
            line = None
            try:
                with self._queue_lock:
                    if self._queue_path.exists():
                        with open(self._queue_path, 'r', encoding='utf-8') as qf:
                            lines = [l.strip() for l in qf.readlines() if l.strip()]
                        if lines:
                            line = lines[0]
                            with open(self._queue_path, 'w', encoding='utf-8') as qf:
                                qf.write('\n'.join(lines[1:]))
            except Exception:
                time.sleep(5)
                continue

            if not line:
                time.sleep(3)
                continue

            acquired = False
            try:
                acquired = self._move_semaphore.acquire(timeout=1)
                if not acquired:
                    with self._queue_lock:
                        with open(self._queue_path, 'a', encoding='utf-8') as qf:
                            qf.write(line + '\n')
                    time.sleep(5)
                    continue

                ready = wait_for_file_ready(line, timeout=30, poll_interval=1.0)
                if not ready:
                    continue

                if not self._db_path:
                    continue

                core = self._core or MotorOrganizadorCore(self._db_path)
                _, destinos, reglas = core.obtener_configuracion()
                ext = os.path.splitext(line)[1].lower()
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
                if destino_alias and destino_alias in destinos:
                    destino_dir = destinos[destino_alias]
                    os.makedirs(destino_dir, exist_ok=True)
                    asist = AsistenteVigiData()
                    from pathlib import Path as _P
                    p = _P(line)
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
                            self.move_result.emit({"path": str(p), "success": True, "message": f"Movido (cola) a {destino_dir}"})
                        except Exception:
                            pass
            except Exception:
                time.sleep(5)
            finally:
                if acquired:
                    try:
                        self._move_semaphore.release()
                    except Exception:
                        pass