import os
import sqlite3
import threading
from PySide6.QtCore import QObject, Signal, Slot, QThread
from watchdog.observers import Observer
from app.controlador.watcher_worker import WatcherWorker
from pathlib import Path
import traceback


class WatcherThread(QThread):
    """QThread que ejecuta un Observer de watchdog y gestiona reinicios dinámicos."""

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
        try:
            self.stop()
            self.wait(1000)
        except Exception:
            pass

        if not self.isRunning():
            self.start()
