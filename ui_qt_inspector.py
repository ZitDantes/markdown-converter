"""
Panneau inspecteur Qt (droit) — PLO-38.

Ce module n'importe PySide6 qu'à l'instanciation (les classes Qt sont
importées au début car ``QFrame`` est nécessaire à la définition de la
classe). Comme ``ui_qt_file_model``, il *peut* être importé sans Qt
côté tests d'import statiques s'il est encapsulé dans un ``importlib``
défensif — mais en pratique on l'instancie uniquement depuis
``MarkdownConverterQtApp.build()``, qui n'est appelé que quand PySide6
est présent.

Vue d'ensemble :

- ``MarkdownInspectorPanel`` est un ``QFrame`` qui contient un
  ``QTabWidget`` à 3 onglets : **Aperçu**, **Sortie**, **Détails**.
- Pour cette PR (commit 2/5), seul l'onglet **Aperçu** est garni.
  Les deux autres sont des placeholders cliquables affichant un message
  explicite ; ils seront remplis par les commits 3, 4, 5.
- ``set_record(record_or_none)`` met à jour l'onglet Aperçu (et restera
  le point d'entrée unique pour les onglets futurs).
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from converter import ConversionStatus, FileConversionRecord
from ui_qt_inspector_data import parse_front_matter

if TYPE_CHECKING:
    pass


# --- Couleurs et polices ----------------------------------------------------
# Alignées sur ``design_handoff_ui_refonte/README.md``.
_WARNING_TEXT_HEX = "#b06a00"
_WARNING_BG_HEX = "#fff4e0"
_YAML_KEY_HEX = "#2b6cb0"
_YAML_VALUE_HEX = "#1f2937"
_MONO_FAMILY = "SF Mono, Menlo, Consolas, monospace"

# Statuts pour lesquels l'aperçu Markdown est pertinent.
_PREVIEWABLE_STATUSES: frozenset[ConversionStatus] = frozenset(
    {
        ConversionStatus.SUCCESS,
        ConversionStatus.SUCCESS_REVIEW,
        ConversionStatus.SUCCESS_FALLBACK,
    }
)


def _mono_font() -> QFont:
    font = QFont(_MONO_FAMILY)
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setFixedPitch(True)
    return font


def _build_preview_yaml_html(front_matter: dict[str, str]) -> str:
    """Rend le front-matter en HTML avec clés colorées (police déjà monospace via QFont)."""
    if not front_matter:
        return ""
    lines: list[str] = []
    lines.append('<pre style="margin:0;">')
    for key, value in front_matter.items():
        k = html.escape(key)
        v = html.escape(value)
        lines.append(
            f'<span style="color:{_YAML_KEY_HEX};font-weight:600;">{k}</span>'
            f'<span style="color:{_YAML_VALUE_HEX};">: "{v}"</span>'
        )
    lines.append("</pre>")
    return "\n".join(lines)


def _placeholder_tab(message: str, object_name: str) -> QWidget:
    """Onglet placeholder utilisé pour Sortie / Détails (commits 3-5)."""
    widget = QFrame()
    widget.setObjectName(object_name)
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(16, 16, 16, 16)
    label = QLabel(message, widget)
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
    label.setObjectName(f"{object_name}_label")
    layout.addWidget(label, stretch=1)
    return widget


class MarkdownInspectorPanel(QFrame):
    """Panneau droit avec onglets Aperçu / Sortie / Détails (PLO-38).

    Exposé en tant que ``QFrame`` pour pouvoir être inséré dans un
    ``QSplitter`` et conserver les helpers (``setObjectName``, etc.)
    utilisés par les tests offscreen.
    """

    OBJECT_NAME = "inspector"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(self.OBJECT_NAME)
        self.setFrameShape(QFrame.Shape.StyledPanel)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._tabs = QTabWidget(self)
        self._tabs.setObjectName("inspector_tabs")

        self._preview_tab = self._build_preview_tab()
        self._output_tab = _placeholder_tab(
            "Onglet « Sortie » — disponible dans le prochain commit (chemin .md, "
            "copie et renommage en lot).",
            "inspector_tab_output",
        )
        self._details_tab = _placeholder_tab(
            "Onglet « Détails » — disponible dans un commit ultérieur (format, "
            "taille, moteur, badge « secours », message d'erreur typé).",
            "inspector_tab_details",
        )

        self._tabs.addTab(self._preview_tab, "Aperçu")
        self._tabs.addTab(self._output_tab, "Sortie")
        self._tabs.addTab(self._details_tab, "Détails")
        outer.addWidget(self._tabs)

        self._current_record: FileConversionRecord | None = None
        self._render_empty_state()

    # --- Construction de l'onglet Aperçu ------------------------------------

    def _build_preview_tab(self) -> QWidget:
        widget = QFrame()
        widget.setObjectName("inspector_tab_preview")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._preview_message = QLabel("", widget)
        self._preview_message.setObjectName("inspector_preview_message")
        self._preview_message.setWordWrap(True)
        self._preview_message.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._preview_message)

        self._preview_warning = QLabel("", widget)
        self._preview_warning.setObjectName("inspector_preview_warning")
        self._preview_warning.setWordWrap(True)
        self._preview_warning.setVisible(False)
        self._preview_warning.setStyleSheet(
            f"QLabel#inspector_preview_warning {{"
            f"  color: {_WARNING_TEXT_HEX};"
            f"  background-color: {_WARNING_BG_HEX};"
            f"  border-left: 3px solid {_WARNING_TEXT_HEX};"
            f"  padding: 6px 8px;"
            f"}}"
        )
        layout.addWidget(self._preview_warning)

        self._preview_yaml = QTextEdit(widget)
        self._preview_yaml.setObjectName("inspector_preview_yaml")
        self._preview_yaml.setReadOnly(True)
        self._preview_yaml.setFont(_mono_font())
        self._preview_yaml.setMaximumHeight(160)
        self._preview_yaml.setVisible(False)
        layout.addWidget(self._preview_yaml)

        self._preview_body = QTextEdit(widget)
        self._preview_body.setObjectName("inspector_preview_body")
        self._preview_body.setReadOnly(True)
        self._preview_body.setFont(_mono_font())
        self._preview_body.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self._preview_body, stretch=1)

        return widget

    # --- API publique --------------------------------------------------------

    def set_record(self, record: FileConversionRecord | None) -> None:
        """Met à jour l'inspecteur pour le record sélectionné (ou ``None``)."""
        self._current_record = record
        if record is None:
            self._render_empty_state()
            return
        if record.status not in _PREVIEWABLE_STATUSES:
            self._render_non_success(record)
            return
        self._render_preview(record)

    def current_record(self) -> FileConversionRecord | None:
        return self._current_record

    # --- Rendu interne -------------------------------------------------------

    def _render_empty_state(self) -> None:
        self._preview_message.setText(
            "Sélectionnez un fichier dans la file pour afficher son aperçu."
        )
        self._preview_message.setVisible(True)
        self._preview_warning.clear()
        self._preview_warning.setVisible(False)
        self._preview_yaml.clear()
        self._preview_yaml.setVisible(False)
        self._preview_body.clear()

    def _render_non_success(self, record: FileConversionRecord) -> None:
        msg = record.message or "Aucun Markdown disponible pour ce fichier."
        self._preview_message.setText(msg)
        self._preview_message.setVisible(True)
        self._preview_warning.clear()
        self._preview_warning.setVisible(False)
        self._preview_yaml.clear()
        self._preview_yaml.setVisible(False)
        self._preview_body.clear()

    def _render_preview(self, record: FileConversionRecord) -> None:
        text = _read_markdown_text(record)
        if text is None:
            self._preview_message.setText(
                "Le fichier Markdown produit est introuvable ou illisible."
            )
            self._preview_message.setVisible(True)
            self._preview_warning.clear()
            self._preview_warning.setVisible(False)
            self._preview_yaml.clear()
            self._preview_yaml.setVisible(False)
            self._preview_body.clear()
            return

        parsed = parse_front_matter(text)
        warning = parsed.front_matter.get("avertissement", "").strip()
        if warning:
            self._preview_warning.setText(f"⚠ {warning}")
            self._preview_warning.setVisible(True)
        else:
            self._preview_warning.clear()
            self._preview_warning.setVisible(False)

        if parsed.front_matter:
            self._preview_yaml.setHtml(_build_preview_yaml_html(parsed.front_matter))
            self._preview_yaml.setVisible(True)
        else:
            self._preview_yaml.clear()
            self._preview_yaml.setVisible(False)

        self._preview_message.setVisible(False)
        self._preview_message.clear()
        self._preview_body.setPlainText(parsed.body)


def _read_markdown_text(record: FileConversionRecord) -> str | None:
    """Récupère le Markdown produit (mémoire en priorité, sinon disque)."""
    if record.output_md_text is not None:
        return record.output_md_text
    out_path: Path | None = record.output_path
    if out_path is None:
        return None
    try:
        return out_path.read_text(encoding="utf-8")
    except OSError:
        return None
