"""
Panneau journal Qt (PLO-37) : tiroir bas, filtres par niveau, lien fichier de log.

Les entrées sont conservées en mémoire ; un changement de filtre réaffiche
depuis cette liste (pas de relecture du fichier ``run.log``).
"""

from __future__ import annotations

import html
from collections import Counter

from PySide6.QtCore import Qt, QUrl, Slot
from PySide6.QtGui import QDesktopServices, QTextCursor
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from logging_setup import get_log_file_path
from ui import LEVEL_COLOR, LEVEL_PREFIX

# Clés de filtre (alignées sur les niveaux logging / converter).
_FILTER_ALL = "ALL"
_FILTER_INFO = "INFO"
_FILTER_WARNING = "WARNING"
_FILTER_ERROR = "ERROR"


class ConversionJournalPanel(QFrame):
    """Journal repliable : stockage RAM, préfixes/couleurs comme ``ui.py``."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("conversion_journal")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._entries: list[tuple[str, str]] = []
        self._filter_key: str = _FILTER_ALL

        header = QHBoxLayout()
        header.setContentsMargins(8, 6, 8, 4)
        header.setSpacing(6)

        self._btn_all = QPushButton(self._label_with_count("Tout", 0))
        self._btn_info = QPushButton(self._label_with_count("Info", 0))
        self._btn_warn = QPushButton(self._label_with_count("Warn", 0))
        self._btn_error = QPushButton(self._label_with_count("Error", 0))
        for b in (self._btn_all, self._btn_info, self._btn_warn, self._btn_error):
            b.setCheckable(True)
            b.setAutoExclusive(False)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._btn_all.setChecked(True)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._group.addButton(self._btn_all, 0)
        self._group.addButton(self._btn_info, 1)
        self._group.addButton(self._btn_warn, 2)
        self._group.addButton(self._btn_error, 3)
        self._group.idClicked.connect(self._on_filter_group_id)

        header.addWidget(self._btn_all)
        header.addWidget(self._btn_info)
        header.addWidget(self._btn_warn)
        header.addWidget(self._btn_error)
        header.addStretch(1)

        self._open_log = QLabel(
            '<a href="openlog">Ouvrir le fichier de log</a>',
            self,
        )
        self._open_log.setTextFormat(Qt.TextFormat.RichText)
        self._open_log.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self._open_log.linkActivated.connect(self._on_open_log_link)

        header.addWidget(self._open_log)

        self._text = QTextEdit(self)
        self._text.setReadOnly(True)
        self._text.setAcceptRichText(True)
        self._text.setMinimumHeight(140)
        self._text.setMaximumHeight(360)
        self._text.setPlaceholderText("Les messages de conversion apparaîtront ici.")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 4)
        root.setSpacing(0)
        root.addLayout(header)
        root.addWidget(self._text, stretch=1)

    @staticmethod
    def _label_with_count(label: str, n: int) -> str:
        return f"{label} ({n})"

    def _counts(self) -> Counter[str]:
        c: Counter[str] = Counter()
        for level, _msg in self._entries:
            c[level] += 1
        c[_FILTER_ALL] = len(self._entries)
        return c

    def _update_filter_button_labels(self) -> None:
        counts = self._counts()
        total = counts[_FILTER_ALL]
        self._btn_all.setText(self._label_with_count("Tout", total))
        self._btn_info.setText(self._label_with_count("Info", counts["INFO"]))
        self._btn_warn.setText(self._label_with_count("Warn", counts["WARNING"]))
        self._btn_error.setText(self._label_with_count("Error", counts["ERROR"]))

    def _on_filter_group_id(self, button_id: int) -> None:
        mapping = {
            0: _FILTER_ALL,
            1: _FILTER_INFO,
            2: _FILTER_WARNING,
            3: _FILTER_ERROR,
        }
        self._filter_key = mapping.get(button_id, _FILTER_ALL)
        self._rebuild_visible_document()

    def _entry_visible_for_filter(self, level: str) -> bool:
        if self._filter_key == _FILTER_ALL:
            return True
        return level == self._filter_key

    def _format_line_html(self, level: str, message: str) -> str:
        prefix = LEVEL_PREFIX.get(level, f"[{level}] ")
        esc_p = html.escape(prefix, quote=False)
        esc_m = html.escape(message, quote=False)
        color = LEVEL_COLOR.get(level)
        if color:
            esc_c = html.escape(color, quote=True)
            inner = f'<span style="color:{esc_c}">{esc_p}{esc_m}</span>'
        else:
            inner = f"{esc_p}{esc_m}"
        return f'<p style="margin:2px 0;line-height:1.35;">{inner}</p>'

    def _rebuild_visible_document(self) -> None:
        parts: list[str] = []
        for level, message in self._entries:
            if self._entry_visible_for_filter(level):
                parts.append(self._format_line_html(level, message))
        body = "".join(parts)
        self._text.setHtml(
            f'<body style="font-family: system-ui, sans-serif; font-size:13px;">{body}</body>'
        )
        self._text.moveCursor(QTextCursor.MoveOperation.End)

    @Slot(str, str)
    def append_log(self, level: str, message: str) -> None:
        """Slot thread-safe (signal Qt depuis le worker) : ajoute une ligne."""
        self._entries.append((level, message))
        self._update_filter_button_labels()
        self._rebuild_visible_document()

    @Slot(str)
    def _on_open_log_link(self, _href: str) -> None:
        path = get_log_file_path()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

    def clear(self) -> None:
        """Vide le journal (utile pour tests ou futur « nouvelle session »)."""
        self._entries.clear()
        self._update_filter_button_labels()
        self._text.clear()
