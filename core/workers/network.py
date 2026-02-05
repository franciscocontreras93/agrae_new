import asyncio
from typing import Any, Callable, Optional

from qgis.PyQt.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
from qgis.core import QgsMessageLog, Qgis


class _AsyncSignals(QObject):
    done = pyqtSignal(object)
    error = pyqtSignal(str)


class _AsyncRunner(QRunnable):
    def __init__(self, coro):
        super().__init__()
        self.coro = coro
        self.signals = _AsyncSignals()

    def run(self):
        try:
            result = asyncio.run(self.coro)
            self.signals.done.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))


def _noop(*args, **kwargs):
    return None