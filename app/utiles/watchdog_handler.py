import os
import sqlite3
from PySide6.QtCore import QMutex, QMutexLocker
from watchdog.events import FileSystemEventHandler


class WatchdogHandler(FileSystemEventHandler):
    """Manejador de eventos para watchdog.

    - No mueve archivos: solo encola rutas en una cola thread-safe.
    - Filtra duplicados usando un conjunto temporal.
    - Ignora directorios y archivos temporales comunes (extensiones/flags de descarga).
    """

    def __init__(self, watch_root=None, event_queue=None, queued_paths=None, queue_lock=None, db_path=None):
        FileSystemEventHandler.__init__(self)
        self.watch_root = os.path.abspath(watch_root) if watch_root else None
        self.event_queue = event_queue
        self.queued_paths = queued_paths if queued_paths is not None else set()
        self.queue_lock = queue_lock if queue_lock is not None else QMutex()
        self.db_path = db_path

    def set_db_path(self, db_path):
        self.db_path = db_path

    def _load_keyword_filters(self):
        if not self.db_path:
            return []

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT palabras_clave FROM reglas_organizacion WHERE activa = 1 AND palabras_clave IS NOT NULL AND palabras_clave != ''"
            )
            filas = cursor.fetchall()
            conn.close()
            keywords = []
            for fila in filas:
                valores = str(fila[0]).split(',')
                for valor in valores:
                    texto = valor.strip().lower()
                    if texto:
                        keywords.append(texto)
            return keywords
        except Exception:
            return []

    def _matches_keywords(self, path: str) -> bool:
        keywords = self._load_keyword_filters()
        if not keywords:
            return True

        nombre = os.path.basename(path).lower()
        for palabra in keywords:
            if palabra in nombre:
                return True
        return False

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

    def _enqueue_if_valid(self, path: str, event_type: str):
        try:
            abs_path = os.path.abspath(path)
            if self._should_ignore(abs_path):
                return

            with QMutexLocker(self.queue_lock):
                if abs_path in self.queued_paths:
                    return
                self.queued_paths.add(abs_path)

            if self.event_queue is not None:
                self.event_queue.put((abs_path, event_type))
        except Exception:
            pass
    def on_created(self, event):
        self._enqueue_if_valid(event.src_path, 'created')

    def on_modified(self, event):
        self._enqueue_if_valid(event.src_path, 'modified')

    def on_moved(self, event):
        dest = getattr(event, 'dest_path', None)
        if dest:
            self._enqueue_if_valid(dest, 'moved')
