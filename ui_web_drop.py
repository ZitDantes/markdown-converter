"""
Glisser-déposer natif sur ``QWebEngineView`` (PLO-53).

L'API HTML5 ``DataTransfer`` dans WebEngine ne expose pas les chemins absolus du
système de fichiers de façon fiable pour une app bureau ; on intercepte le DnD au
niveau Qt (même logique que ``ui_qt_file_drop_table``) et on notifie le front via
les signaux ``WebBackend``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWebEngineWidgets import QWebEngineView

from ui_qt_file_drop_table import supported_paths_from_mime

if TYPE_CHECKING:
    from ui_web_shell import WebBackend


class WebEngineDropView(QWebEngineView):
    """``QWebEngineView`` qui accepte le dépôt de fichiers/dossiers depuis le bureau."""

    def __init__(self, backend: WebBackend, parent: object | None = None) -> None:
        super().__init__(parent)
        self._backend = backend
        self.setAcceptDrops(True)

    def _mime_supported(self, mime: object) -> bool:
        from PySide6.QtCore import QMimeData

        if not isinstance(mime, QMimeData):
            return False
        return bool(supported_paths_from_mime(mime))

    def _set_overlay(self, visible: bool) -> None:
        self._backend.dropOverlayVisible.emit(visible)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._mime_supported(event.mimeData()):
            event.acceptProposedAction()
            self._set_overlay(True)
        else:
            event.ignore()
            self._set_overlay(False)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if self._mime_supported(event.mimeData()):
            event.acceptProposedAction()
            self._set_overlay(True)
        else:
            event.ignore()
            self._set_overlay(False)

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._set_overlay(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        self._set_overlay(False)
        if self._mime_supported(event.mimeData()):
            self._backend.handle_drop_mime(event.mimeData())
            event.acceptProposedAction()
        else:
            event.ignore()
