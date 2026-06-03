import os
import time
import threading
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
from .watchdog_handler import WatchdogHandler
from .file_waiter import wait_for_file_ready
from app.controlador.controlador_asistente import AsistenteVigiData
from app.core.motor_organizador import MotorOrganizadorCore
print("DEBUG: Cargando watcher_worker.py...")
from pathlib import Path
print(f"DEBUG: Path es: {type(Path)}")

class WatcherWorker(QObject):
    """Conecta el WatchdogHandler con la lógica de espera (Fase 2).

    - Escucha `file_detected` y en un hilo separado espera hasta que el archivo esté libre.
    - No mueve archivos; emite `file_ready` cuando esté listo.
    """

    file_ready = Signal(str)
    # Señal que notifica el resultado del intento de movimiento: dict {path, success, message}
    move_result = Signal(dict)

    def __init__(self, watch_root=None, parent=None):
        super().__init__(parent)
        self.handler = WatchdogHandler(watch_root=watch_root)
        self.handler.file_detected.connect(self._on_file_detected)
        self._db_path = None

    def set_db_path(self, db_path):
        self._db_path = db_path

    @Slot(str)
    def _on_file_detected(self, path: str):
        # Ejecutar la espera en un hilo para no bloquear el event loop
        t = threading.Thread(target=self._wait_and_emit, args=(path,), daemon=True)
        t.start()

    def _wait_and_emit(self, path: str):
        # Ignorar extensiones temporales comunes inmediatamente
        lower = path.lower()
        if lower.endswith('.crdownload') or lower.endswith('.part') or lower.endswith('.tmp'):
            try:
                print(f"[watcher_worker] ignoring temporary file: {path}")
            except Exception:
                pass
            return

        # Esperar hasta que el archivo esté listo (timeout opcional)
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
            # Emitir y además procesar regla/movimiento si hay DB configurada
            self.file_ready.emit(path)
            try:
                # Procesamiento inmediato: consultar reglas y mover si aplica
                if self._db_path:
                    core = MotorOrganizadorCore(self._db_path)
                    _, destinos, reglas = core.obtener_configuracion()

                    ext = os.path.splitext(path)[1].lower().lstrip('.')
                    destino_alias = None
                    for regla in reglas:
                        if regla.get('extension') == ext or regla.get('extension') is None:
                            destino_alias = regla.get('destino_alias')
                            break

                    if destino_alias and destino_alias in destinos:
                        destino_dir = destinos[destino_alias]
                        # Asegurar existencia
                        os.makedirs(destino_dir, exist_ok=True)
                        asist = AsistenteVigiData()
                        try:
                            from pathlib import Path
                            p = Path(path)
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
            except Exception:
                pass
