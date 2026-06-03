from watchdog.events import FileSystemEventHandler
from PySide6.QtCore import QObject, Signal
import os


class WatchdogHandler(FileSystemEventHandler, QObject):
    """Manejador de eventos para watchdog.

    - No mueve archivos, solo emite la ruta detectada mediante la señal `file_detected`.
    - Ignora directorios y archivos temporales comunes (extensiones/flags de descarga).
    """

    file_detected = Signal(str)

    def __init__(self, watch_root=None):
        QObject.__init__(self)
        FileSystemEventHandler.__init__(self)
        self.watch_root = os.path.abspath(watch_root) if watch_root else None

    def _should_ignore(self, path: str) -> bool:
        if os.path.isdir(path):
            return True

        name = os.path.basename(path)
        tmp_indicators = (".part", ".crdownload", ".tmp", "~")
        if any(name.endswith(ind) for ind in tmp_indicators):
            return True
        if name.startswith('.'):
            return True

        if self.watch_root and not os.path.commonpath([self.watch_root, os.path.abspath(path)]) == self.watch_root:
            return True

        return False

    def _emit_if_valid(self, path: str):
        try:
            if not self._should_ignore(path):
                abs_path = os.path.abspath(path)
                try:
                    print(f"[watchdog_handler] detected: {abs_path}")
                except Exception:
                    pass
                self.file_detected.emit(abs_path)
        except Exception:
            pass

    def on_created(self, event):
        self._emit_if_valid(event.src_path)

    def on_moved(self, event):
        dest = getattr(event, 'dest_path', None)
        if dest:
            self._emit_if_valid(dest)
