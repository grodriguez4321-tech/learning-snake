"""Background execution helpers so subprocess work never freezes the Qt UI.

Uses a daemon thread plus a QTimer poll on the GUI thread (same pattern as the
previous Tk queue pump). This avoids fragile QThread ownership/GC issues while
keeping the UI responsive.
"""

from __future__ import annotations

import queue
import threading
from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, QTimer


class AsyncJobHost(QObject):
    """Mixin-style helper: own one of these on the main window."""

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._queue: queue.Queue[tuple[Callable[[Any], None], Any]] = queue.Queue()
        self._closing = False
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._drain)
        self._timer.start()

    def stop(self) -> None:
        self._closing = True
        self._timer.stop()

    def run(
        self,
        work: Callable[[], Any],
        on_done: Callable[[Any], None],
    ) -> None:
        def worker() -> None:
            try:
                result: Any = work()
            except BaseException as exc:  # noqa: BLE001
                result = exc
            if self._closing:
                return
            self._queue.put((on_done, result))

        threading.Thread(target=worker, daemon=True).start()

    def _drain(self) -> None:
        if self._closing:
            return
        try:
            while True:
                callback, payload = self._queue.get_nowait()
                try:
                    callback(payload)
                except Exception:  # noqa: BLE001
                    import traceback

                    traceback.print_exc()
        except queue.Empty:
            pass
