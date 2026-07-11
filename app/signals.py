from PySide6.QtCore import QObject, Signal


class AppSignals(QObject):
    stats_changed = Signal()
    destinos_changed = Signal()
    origenes_changed = Signal()
    solicitar_carpeta_origen = Signal(str)   # emite el alias sugerido
    solicitar_carpeta_destino = Signal(str)  # emite el alias sugerido


app_signals = AppSignals()
