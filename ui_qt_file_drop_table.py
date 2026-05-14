"""
Table de file avec glisser-déposer natif (PLO-27).

Les dépôts depuis le gestionnaire de fichiers exposent en général des ``QUrl``
locales (schéma ``file://``). Le comportement est le même sur macOS, Windows
et Linux tant que ``QMimeData.hasUrls()`` est vrai et que ``QUrl.isLocalFile()``.

Les chemins sont fusionnés via ``utils.merge_file_lists`` (mêmes règles que
l'ajout par boutons : extensions supportées, dossiers parcourus récursivement).

Un ``QFrame`` surélevé affiche le contour pointillé ; il est configuré avec
``WA_TransparentForMouseEvents`` pour que les événements de glisser-déposer
atteignent le ``viewport`` sous-jacent.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import (
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
    QResizeEvent,
)
from PySide6.QtWidgets import QFrame, QLabel, QTableView, QVBoxLayout, QWidget

from ui_qt_file_model import ConversionFileTableModel
from utils import merge_file_lists


def paths_from_mime_urls(mime: QMimeData) -> list[Path]:
    """Extrait les chemins locaux à partir d'un ``QMimeData`` (URLs ``file://``)."""
    if not mime.hasUrls():
        return []
    out: list[Path] = []
    for url in mime.urls():
        if not url.isLocalFile():
            continue
        raw = url.toLocalFile()
        if not raw:
            continue
        out.append(Path(raw))
    return out


def supported_paths_from_mime(mime: QMimeData) -> list[Path]:
    """Chemins de fichiers supportés issus d'un glisser-déposer (fichiers + dossiers)."""
    paths = paths_from_mime_urls(mime)
    files = [p for p in paths if p.exists() and p.is_file()]
    dirs = [p for p in paths if p.exists() and p.is_dir()]
    supported, _unsupported = merge_file_lists(files, dirs)
    return supported


class ConversionFileDropTableView(QTableView):
    """``QTableView`` qui accepte le dépôt de fichiers et dossiers sur la zone liste."""

    def __init__(
        self, source_model: ConversionFileTableModel, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._source_model = source_model
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)

        self._drop_frame = QFrame(self)
        self._drop_frame.setObjectName("file_view_drop_overlay")
        self._drop_frame.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._drop_frame.hide()
        self._drop_frame.setStyleSheet(
            "QFrame#file_view_drop_overlay {"
            " background-color: rgba(10, 122, 255, 0.10);"
            " border: 2px dashed #0a7aff;"
            " border-radius: 10px;"
            "}"
        )
        inner = QVBoxLayout(self._drop_frame)
        inner.setContentsMargins(12, 12, 12, 12)
        inner.addStretch(1)
        hint = QLabel("Déposer pour ajouter à la file…", self._drop_frame)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #0a7aff; font-weight: 600; font-size: 14px;")
        inner.addWidget(hint)
        inner.addStretch(1)

    def _position_drop_frame(self) -> None:
        self._drop_frame.setGeometry(self.viewport().geometry())
        self._drop_frame.raise_()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._position_drop_frame()

    def _set_drop_overlay_visible(self, visible: bool) -> None:
        if visible:
            self._position_drop_frame()
            self._drop_frame.show()
        else:
            self._drop_frame.hide()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if supported_paths_from_mime(event.mimeData()):
            event.acceptProposedAction()
            self._set_drop_overlay_visible(True)
        else:
            event.ignore()
            self._set_drop_overlay_visible(False)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if supported_paths_from_mime(event.mimeData()):
            event.acceptProposedAction()
            self._set_drop_overlay_visible(True)
        else:
            event.ignore()
            self._set_drop_overlay_visible(False)

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._set_drop_overlay_visible(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        self._set_drop_overlay_visible(False)
        to_add = supported_paths_from_mime(event.mimeData())
        if to_add:
            # Import paresseux : évite un cycle ``ui_qt`` ↔ ce module au chargement.
            from ui_qt import add_paths_to_model

            add_paths_to_model(self._source_model, to_add)
            event.acceptProposedAction()
        else:
            event.ignore()
