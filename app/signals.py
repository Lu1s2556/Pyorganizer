from PySide6.QtCore import QObject, Signal


class AppSignals(QObject):
    stats_changed = Signal()


app_signals = AppSignals()
