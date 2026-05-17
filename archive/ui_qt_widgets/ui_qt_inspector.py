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
- L'onglet **Aperçu** affiche le Markdown produit (mémoire ou disque).
- L'onglet **Sortie** affiche le chemin ``.md``, copie / dossier parent, et le
  **renommage en lot** (préfixe, suffixe, casse, aperçu live, application
  atomique après validation).
- L'onglet **Détails** résume extension, taille source, statut, moteur,
  indicateur **secours Pandoc**, type d'erreur et message le cas échéant.
- ``set_record(record_or_none)`` met à jour les onglets pour le record
  sélectionné (ou ``None``).
- ``set_file_model(model)`` relie le renommage en lot à la file (appelé depuis
  ``MarkdownConverterQtApp.build()``).
"""

from __future__ import annotations

import html
from contextlib import suppress
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from converter import ConversionStatus, FileConversionRecord
from ui_conversion_display import (
    conversion_status_label_fr,
    format_source_file_size,
)
from ui_qt_file_model import ConversionFileTableModel
from ui_qt_inspector_data import parse_front_matter
from ui_qt_inspector_rename import (
    CASE_LOWER,
    CASE_TITLE,
    CASE_UNCHANGED,
    CASE_UPPER,
    build_new_output_path,
    execute_rename_plan,
    plan_bulk_rename,
)
from utils import normalize_extension

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
        self._output_tab = self._build_output_tab()
        self._details_tab = self._build_details_tab()

        self._tabs.addTab(self._preview_tab, "Aperçu")
        self._tabs.addTab(self._output_tab, "Sortie")
        self._tabs.addTab(self._details_tab, "Détails")
        outer.addWidget(self._tabs)

        self._current_record: FileConversionRecord | None = None
        self._resolved_output_path: Path | None = None
        self._file_model: ConversionFileTableModel | None = None
        self._render_empty_state()
        self._refresh_output_tab(None)
        self._refresh_details_tab(None)

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

    def _build_output_tab(self) -> QWidget:
        """Onglet Sortie : chemin ``.md``, copie presse-papiers, ouverture du dossier parent."""
        widget = QFrame()
        widget.setObjectName("inspector_tab_output")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._output_info = QLabel("", widget)
        self._output_info.setObjectName("inspector_output_info")
        self._output_info.setWordWrap(True)
        layout.addWidget(self._output_info)

        self._output_path = QLineEdit(widget)
        self._output_path.setObjectName("inspector_output_path")
        self._output_path.setReadOnly(True)
        self._output_path.setFont(_mono_font())
        self._output_path.setPlaceholderText("—")
        layout.addWidget(self._output_path)

        row = QHBoxLayout()
        row.setSpacing(8)
        self._output_copy = QPushButton("Copier le chemin", widget)
        self._output_copy.setObjectName("inspector_output_copy")
        self._output_copy.setToolTip(
            "Copier le chemin absolu du fichier Markdown dans le presse-papiers."
        )
        self._output_open_folder = QPushButton("Ouvrir le dossier", widget)
        self._output_open_folder.setObjectName("inspector_output_open_folder")
        self._output_open_folder.setToolTip(
            "Ouvrir le dossier contenant le fichier Markdown dans le Finder ou l'explorateur."
        )
        row.addWidget(self._output_copy)
        row.addWidget(self._output_open_folder)
        row.addStretch(1)
        layout.addLayout(row)

        self._output_copy.clicked.connect(self._on_output_copy_path)
        self._output_open_folder.clicked.connect(self._on_output_open_folder)

        line_bulk = QFrame(widget)
        line_bulk.setFrameShape(QFrame.Shape.HLine)
        line_bulk.setObjectName("inspector_output_bulk_separator")
        layout.addWidget(line_bulk)

        bulk_title = QLabel(
            "Renommage en lot : s'applique à tous les fichiers Markdown produits listés dans la file.",
            widget,
        )
        bulk_title.setObjectName("inspector_output_bulk_title")
        bulk_title.setWordWrap(True)
        layout.addWidget(bulk_title)

        affix_row = QHBoxLayout()
        affix_row.setSpacing(8)
        affix_row.addWidget(QLabel("Préfixe", widget))
        self._bulk_prefix = QLineEdit(widget)
        self._bulk_prefix.setObjectName("inspector_bulk_prefix")
        self._bulk_prefix.setPlaceholderText("ex. rapport_")
        affix_row.addWidget(self._bulk_prefix, stretch=1)
        affix_row.addWidget(QLabel("Suffixe", widget))
        self._bulk_suffix = QLineEdit(widget)
        self._bulk_suffix.setObjectName("inspector_bulk_suffix")
        self._bulk_suffix.setPlaceholderText("ex. _v2")
        affix_row.addWidget(self._bulk_suffix, stretch=1)
        affix_row.addWidget(QLabel("Casse", widget))
        self._bulk_case = QComboBox(widget)
        self._bulk_case.setObjectName("inspector_bulk_case")
        self._bulk_case.addItem("Inchangé", CASE_UNCHANGED)
        self._bulk_case.addItem("minuscules", CASE_LOWER)
        self._bulk_case.addItem("MAJUSCULES", CASE_UPPER)
        self._bulk_case.addItem("Format titre", CASE_TITLE)
        affix_row.addWidget(self._bulk_case)
        layout.addLayout(affix_row)

        self._bulk_preview = QLabel("", widget)
        self._bulk_preview.setObjectName("inspector_bulk_preview")
        self._bulk_preview.setWordWrap(True)
        self._bulk_preview.setFont(_mono_font())
        layout.addWidget(self._bulk_preview)

        self._bulk_plan_error = QLabel("", widget)
        self._bulk_plan_error.setObjectName("inspector_bulk_plan_error")
        self._bulk_plan_error.setWordWrap(True)
        self._bulk_plan_error.setStyleSheet("color: #b00020;")
        self._bulk_plan_error.hide()
        layout.addWidget(self._bulk_plan_error)

        self._bulk_apply = QPushButton("Appliquer le renommage en lot", widget)
        self._bulk_apply.setObjectName("inspector_bulk_apply")
        self._bulk_apply.setToolTip(
            "Renomme sur le disque tous les fichiers .md de sortie de la file. "
            "Si une cible existe déjà, aucun fichier n'est modifié."
        )
        layout.addWidget(self._bulk_apply)

        self._bulk_prefix.textChanged.connect(self._sync_bulk_rename_ui)
        self._bulk_suffix.textChanged.connect(self._sync_bulk_rename_ui)
        self._bulk_case.currentIndexChanged.connect(self._sync_bulk_rename_ui)
        self._bulk_apply.clicked.connect(self._on_bulk_rename_apply)

        return widget

    def _build_details_tab(self) -> QWidget:
        """Onglet Détails : extension, taille, statut, moteur, secours Pandoc, erreur, message."""
        widget = QFrame()
        widget.setObjectName("inspector_tab_details")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._details_hint = QLabel("", widget)
        self._details_hint.setObjectName("inspector_details_hint")
        self._details_hint.setWordWrap(True)
        layout.addWidget(self._details_hint)

        form_host = QWidget(widget)
        form = QFormLayout(form_host)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(6)

        def value_label(object_name: str) -> QLabel:
            lbl = QLabel("—", form_host)
            lbl.setObjectName(object_name)
            lbl.setWordWrap(True)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            return lbl

        self._detail_format = value_label("inspector_detail_format")
        form.addRow("Extension source", self._detail_format)

        self._detail_size = value_label("inspector_detail_size")
        form.addRow("Taille source", self._detail_size)

        self._detail_status = value_label("inspector_detail_status")
        form.addRow("Statut", self._detail_status)

        self._detail_engine = value_label("inspector_detail_engine")
        form.addRow("Moteur", self._detail_engine)

        self._detail_fallback = value_label("inspector_detail_fallback")
        form.addRow("Secours Pandoc", self._detail_fallback)

        self._detail_error_type = value_label("inspector_detail_error_type")
        form.addRow("Type d'erreur", self._detail_error_type)

        self._detail_message = QTextEdit(form_host)
        self._detail_message.setObjectName("inspector_detail_message")
        self._detail_message.setReadOnly(True)
        self._detail_message.setMaximumHeight(120)
        self._detail_message.setPlaceholderText("—")
        form.addRow("Message", self._detail_message)

        layout.addWidget(form_host, stretch=1)
        return widget

    # --- API publique --------------------------------------------------------

    def set_record(self, record: FileConversionRecord | None) -> None:
        """Met à jour l'inspecteur pour le record sélectionné (ou ``None``)."""
        self._current_record = record
        if record is None:
            self._render_empty_state()
        elif record.status not in _PREVIEWABLE_STATUSES:
            self._render_non_success(record)
        else:
            self._render_preview(record)
        self._refresh_output_tab(record)
        self._refresh_details_tab(record)

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

    def _refresh_output_tab(self, record: FileConversionRecord | None) -> None:
        """Met à jour le chemin ``.md`` et l'état des boutons Sortie."""
        self._resolved_output_path = None
        if record is None:
            self._output_info.setText(
                "Sélectionnez un fichier dans la file pour afficher le chemin du Markdown produit."
            )
            self._output_path.clear()
            self._output_copy.setEnabled(False)
            self._output_open_folder.setEnabled(False)
            self._sync_bulk_rename_ui()
            return

        out = record.output_path
        if out is None:
            self._output_info.setText("Aucun fichier Markdown n'est encore associé à cette entrée.")
            self._output_path.clear()
            self._output_copy.setEnabled(False)
            self._output_open_folder.setEnabled(False)
            self._sync_bulk_rename_ui()
            return

        try:
            resolved = out.resolve()
        except OSError:
            resolved = out

        self._resolved_output_path = resolved
        self._output_path.setText(str(resolved))
        self._output_info.setText(
            "Fichier Markdown produit. Vous pouvez copier le chemin absolu ou ouvrir son dossier parent."
        )
        self._output_copy.setEnabled(True)
        self._output_open_folder.setEnabled(True)
        self._sync_bulk_rename_ui()

    def _refresh_details_tab(self, record: FileConversionRecord | None) -> None:
        """Met à jour l'onglet Détails (extension, taille, statut, moteur, diagnostic)."""
        _fallback_yes_style = (
            "QLabel { background-color: #e3f2fd; color: #0b66c2; "
            "padding: 4px 8px; border-radius: 4px; }"
        )
        if record is None:
            self._details_hint.setVisible(True)
            self._details_hint.setText(
                "Sélectionnez un fichier dans la file pour afficher format, taille, moteur et diagnostic."
            )
            self._detail_format.setText("—")
            self._detail_size.setText("—")
            self._detail_status.setText("—")
            self._detail_engine.setText("—")
            self._detail_fallback.setText("—")
            self._detail_fallback.setStyleSheet("")
            self._detail_fallback.setToolTip("")
            self._detail_error_type.setText("—")
            self._detail_message.clear()
            return

        self._details_hint.setVisible(False)
        self._details_hint.clear()

        ext = normalize_extension(record.source_path)
        self._detail_format.setText(ext or "—")
        self._detail_size.setText(format_source_file_size(record.source_path))
        self._detail_status.setText(conversion_status_label_fr(record.status))
        self._detail_engine.setText(record.engine_used or "—")

        if record.used_pandoc_fallback:
            self._detail_fallback.setText("Oui")
            self._detail_fallback.setStyleSheet(_fallback_yes_style)
            self._detail_fallback.setToolTip(
                "Ce Markdown a été produit (en tout ou en partie) via le moteur de secours Pandoc."
            )
        else:
            self._detail_fallback.setText("Non")
            self._detail_fallback.setStyleSheet("")
            self._detail_fallback.setToolTip("")

        self._detail_error_type.setText(record.error_type or "—")
        self._detail_message.setPlainText((record.message or "").strip())

    def _on_output_copy_path(self) -> None:
        if self._resolved_output_path is None:
            return
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(str(self._resolved_output_path))

    def _on_output_open_folder(self) -> None:
        if self._resolved_output_path is None:
            return
        parent = self._resolved_output_path.parent
        try:
            folder = str(parent.resolve())
        except OSError:
            folder = str(parent)
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def set_file_model(self, model: ConversionFileTableModel | None) -> None:
        """Branche le renommage en lot sur le modèle de la file (ou ``None``)."""
        if self._file_model is not None:
            for sig in (
                self._file_model.rowsInserted,
                self._file_model.rowsRemoved,
                self._file_model.modelReset,
                self._file_model.dataChanged,
            ):
                with suppress(TypeError):
                    sig.disconnect(self._sync_bulk_rename_ui)
        self._file_model = model
        if model is not None:
            model.rowsInserted.connect(self._sync_bulk_rename_ui)
            model.rowsRemoved.connect(self._sync_bulk_rename_ui)
            model.modelReset.connect(self._sync_bulk_rename_ui)
            model.dataChanged.connect(self._sync_bulk_rename_ui)
        self._sync_bulk_rename_ui()

    def _bulk_case_mode(self) -> str:
        raw = self._bulk_case.currentData(Qt.ItemDataRole.UserRole)
        return raw if isinstance(raw, str) else CASE_UNCHANGED

    def _sync_bulk_rename_ui(self) -> None:
        """Aperçu live du nom cible + validation du plan en lot."""
        if self._file_model is None:
            for w in (self._bulk_prefix, self._bulk_suffix, self._bulk_case, self._bulk_apply):
                w.setEnabled(False)
            self._bulk_preview.setText("—")
            self._bulk_plan_error.clear()
            self._bulk_plan_error.hide()
            return

        for w in (self._bulk_prefix, self._bulk_suffix, self._bulk_case, self._bulk_apply):
            w.setEnabled(True)

        prefix = self._bulk_prefix.text()
        suffix = self._bulk_suffix.text()
        case_mode = self._bulk_case_mode()

        rec = self._current_record
        if (
            rec is not None
            and rec.status in _PREVIEWABLE_STATUSES
            and rec.output_path is not None
            and rec.output_path.suffix.lower() == ".md"
        ):
            preview_path = build_new_output_path(rec.output_path, prefix, suffix, case_mode)
            try:
                preview_txt = str(preview_path.resolve())
            except OSError:
                preview_txt = str(preview_path)
            self._bulk_preview.setText(f"Aperçu (fichier sélectionné) : {preview_txt}")
        else:
            self._bulk_preview.setText("Aperçu (fichier sélectionné) : —")

        ops, err = plan_bulk_rename(self._file_model.records(), prefix, suffix, case_mode)
        if err:
            self._bulk_plan_error.setText(err)
            self._bulk_plan_error.show()
            self._bulk_apply.setEnabled(False)
            return

        self._bulk_plan_error.clear()
        self._bulk_plan_error.hide()
        self._bulk_apply.setEnabled(bool(ops))

    def _on_bulk_rename_apply(self) -> None:
        model = self._file_model
        if model is None:
            return
        prefix = self._bulk_prefix.text()
        suffix = self._bulk_suffix.text()
        case_mode = self._bulk_case_mode()
        ops, err = plan_bulk_rename(model.records(), prefix, suffix, case_mode)
        if err:
            QMessageBox.warning(self, "Renommage impossible", err)
            return
        if not ops:
            QMessageBox.information(
                self,
                "Renommage en lot",
                "Aucun fichier à renommer : vérifiez que la file contient des conversions "
                "réussies avec un fichier .md en sortie, ou modifiez préfixe / suffixe / casse.",
            )
            return
        ok, msg = execute_rename_plan(ops)
        if not ok:
            QMessageBox.critical(self, "Renommage en lot", msg)
            return
        model.refresh_all()
        self._refresh_output_tab(self._current_record)
        self._refresh_details_tab(self._current_record)
        self._sync_bulk_rename_ui()


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
