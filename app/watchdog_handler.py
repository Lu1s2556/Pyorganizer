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
        # Ruta raíz a la que queremos limitar eventos (opcional)
        self.watch_root = os.path.abspath(watch_root) if watch_root else None

    def _should_ignore(self, path: str) -> bool:
        # Ignorar directorios
        if os.path.isdir(path):
            return True

        name = os.path.basename(path)
        # Ignorar archivos temporales típicos de navegadores y sistemas
        tmp_indicators = (".part", ".crdownload", ".tmp", "~")
        if any(name.endswith(ind) for ind in tmp_indicators):
            return True
        if name.startswith("."):
            return True

        # Si watch_root está definido, asegúrate de que path esté en esa raíz
        if self.watch_root and not os.path.commonpath([self.watch_root, os.path.abspath(path)]) == self.watch_root:
            return True

        return False

    def _emit_if_valid(self, path: str):
        try:
            if not self._should_ignore(path):
                # Solo emitir la ruta; la lógica de espera/movimiento corresponde al motor
                self.file_detected.emit(os.path.abspath(path))
        except Exception:
            # Protegemos el manejador de errores para no detener el observer
            pass

    def on_created(self, event):
        # event.src_path puede ser archivo o directorio
        self._emit_if_valid(event.src_path)

    def on_moved(self, event):
        # Algunos descargadores renombrarán archivos temporales al final
        # event.dest_path es la nueva ruta final
        dest = getattr(event, 'dest_path', None)
        if dest:
            self._emit_if_valid(dest)
