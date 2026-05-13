"""
Modèle de table Qt pour la file de conversion (PLO-35).

Ce module importe PySide6 au chargement : ne pas l'importer depuis ``ui_qt``
au niveau module (cf. ``main.py`` / tests d'import sans Qt). Le câblage dans
``MarkdownConverterQtApp`` se fera via un import local ou depuis ce module
uniquement lorsque l'UI Qt est active.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from converter import ConversionStatus, FileConversionRecord
from utils import normalize_extension

# Tokens « Couleurs par format » — design_handoff_ui_refonte/README.md
_FORMAT_ACCENT_HEX: dict[str, str] = {
    ".docx": "#2b6cb0",
    ".pdf": "#c0392b",
    ".pptx": "#d35400",
    ".xlsx": "#1e8449",
    ".html": "#6b46c1",
    ".htm": "#6b46c1",
    ".txt": "#4a5568",
}

_DEFAULT_FORMAT_HEX = "#4a5568"

_COL_FORMAT = 0
_COL_NAME = 1
_COL_SIZE = 2
_COL_STATUS = 3
_COL_PROGRESS = 4

_HEADERS = ("Format", "Fichier", "Taille", "Statut", "Progression")


def _format_accent_hex_for_path(path: Path) -> str:
    ext = normalize_extension(path)
    return _FORMAT_ACCENT_HEX.get(ext, _DEFAULT_FORMAT_HEX)


def _format_monogram(path: Path) -> str:
    ext = normalize_extension(path).lstrip(".")
    return (ext[:4] or "?").upper()


def _format_file_size(num_bytes: int) -> str:
    if num_bytes < 0:
        return "—"
    if num_bytes == 0:
        return "0 o"
    units = ("o", "Ko", "Mo", "Go", "To")
    size = float(num_bytes)
    u = 0
    while size >= 1024.0 and u < len(units) - 1:
        size /= 1024.0
        u += 1
    if u == 0:
        return f"{int(size)} {units[u]}"
    text = f"{size:.1f}".rstrip("0").rstrip(".")
    return f"{text} {units[u]}"


def _file_size_bytes(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _status_label_fr(status: ConversionStatus) -> str:
    mapping: dict[ConversionStatus, str] = {
        ConversionStatus.SUCCESS: "OK",
        ConversionStatus.SUCCESS_REVIEW: "OK · relire",
        ConversionStatus.SUCCESS_FALLBACK: "OK · secours",
        ConversionStatus.ERROR: "Erreur",
        ConversionStatus.UNSUPPORTED: "Non pris en charge",
        ConversionStatus.EMPTY: "Vide",
        ConversionStatus.PROCESSING: "En cours",
        ConversionStatus.QUEUED: "En attente",
    }
    return mapping.get(status, status.value)


def _progress_display(progress_percent: float) -> str:
    pct = max(0.0, min(1.0, progress_percent))
    return f"{round(pct * 100)} %"


class ConversionFileTableModel(QAbstractTableModel):
    """``QAbstractTableModel`` branché sur une liste de ``FileConversionRecord``."""

    def __init__(self, records: list[FileConversionRecord] | None = None) -> None:
        super().__init__()
        self._records: list[FileConversionRecord] = list(records or [])

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(self._records)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(_HEADERS)

    def records(self) -> list[FileConversionRecord]:
        """Référence mutable : la même liste que celle affichée par le modèle."""
        return self._records

    def set_records(self, records: list[FileConversionRecord]) -> None:
        self.beginResetModel()
        self._records = list(records)
        self.endResetModel()

    def append_record(self, record: FileConversionRecord) -> None:
        row = len(self._records)
        self.beginInsertRows(QModelIndex(), row, row)
        self._records.append(record)
        self.endInsertRows()

    def clear(self) -> None:
        if not self._records:
            return
        self.beginResetModel()
        self._records.clear()
        self.endResetModel()

    def refresh_row(self, row: int) -> None:
        if row < 0 or row >= len(self._records):
            return
        top_left = self.index(row, 0)
        bottom_right = self.index(row, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right)

    def refresh_all(self) -> None:
        if not self._records:
            return
        top_left = self.index(0, 0)
        bottom_right = self.index(len(self._records) - 1, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> str | None:
        if role != Qt.ItemDataRole.DisplayRole or orientation != Qt.Orientation.Horizontal:
            return None
        if 0 <= section < len(_HEADERS):
            return _HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object | None:
        if not index.isValid() or index.row() >= len(self._records):
            return None
        rec = self._records[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == _COL_FORMAT:
                return _format_monogram(rec.source_path)
            if col == _COL_NAME:
                return rec.source_path.name
            if col == _COL_SIZE:
                return _format_file_size(_file_size_bytes(rec.source_path))
            if col == _COL_STATUS:
                return _status_label_fr(rec.status)
            if col == _COL_PROGRESS:
                return _progress_display(rec.progress_percent)
            return None

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (_COL_SIZE, _COL_PROGRESS):
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        if role == Qt.ItemDataRole.BackgroundRole and col == _COL_FORMAT:
            return QColor(_format_accent_hex_for_path(rec.source_path))

        if role == Qt.ItemDataRole.ForegroundRole and col == _COL_FORMAT:
            return QColor("#ffffff")

        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        if not self._records or column < 0 or column >= len(_HEADERS):
            return

        reverse = order == Qt.SortOrder.DescendingOrder

        def key(rec: FileConversionRecord) -> str | int | float:
            p = rec.source_path
            if column == _COL_FORMAT:
                return normalize_extension(p).lower()
            if column == _COL_NAME:
                return p.name.lower()
            if column == _COL_SIZE:
                return _file_size_bytes(p)
            if column == _COL_STATUS:
                return rec.status.value
            if column == _COL_PROGRESS:
                return rec.progress_percent
            return ""

        self.layoutAboutToBeChanged.emit()
        self._records.sort(key=key, reverse=reverse)
        self.layoutChanged.emit()

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
