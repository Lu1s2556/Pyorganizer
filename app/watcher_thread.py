import os
import sqlite3
from PySide6.QtCore import QThread, Signal
from watchdog.observers import Observer
from app.watcher_worker import WatcherWorker


class WatcherThread(QThread):
    """QThread que ejecuta un Observer de watchdog y gestiona reinicios dinámicos.

    - Carga rutas de origen desde la BD (`carpetas_monitoreadas`)
    - Programa el `WatcherWorker.handler` sobre esas rutas (no recursivo)
    - Soporta `restart()` para recargar rutas en caliente
    """

    started_ok = Signal()
    stopped = Signal()
    error = Signal(str)

    def __init__(self, db_path: str, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self._observer = None
        self._running = False
        self._worker = WatcherWorker()
        self._worker.set_db_path(db_path)

    def run(self):
        try:
            self._observer = Observer()

            rutas = self._load_origenes()
            if not rutas:
                self.error.emit("No hay rutas de origen activas en la base de datos")
                return

            for ruta in rutas:
                try:
                    if os.path.exists(ruta):
                        self._observer.schedule(self._worker.handler, ruta, recursive=False)
                except Exception:
                    pass

            self._observer.start()
            self._running = True
            try:
                self.started_ok.emit()
            except Exception:
                pass

            while self._running:
                self.msleep(200)

        except Exception as e:
            try:
                self.error.emit(str(e))
            except Exception:
                pass
        finally:
            try:
                if self._observer:
                    self._observer.stop()
                    self._observer.join()
            except Exception:
                pass
            try:
                self.stopped.emit()
            except Exception:
                pass

    def _load_origenes(self):
        rutas = []
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT ruta FROM carpetas_monitoreadas WHERE activa = 1")
            rutas = [row[0] for row in cur.fetchall()]
            conn.close()
        except Exception:
            rutas = []
        return rutas

    def stop(self):
        self._running = False

    def restart(self):
        """Detiene y vuelve a iniciar el observer recargando rutas desde la BD."""
        try:
            # stopping will let run() exit and cleanup
            self.stop()
            # wait for thread to finish
            self.wait(1000)
        except Exception:
            pass

        # Create a fresh observer by restarting the thread
        if not self.isRunning():
            self.start()
