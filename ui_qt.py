"""
Interface PySide6 du Markdown Converter (prototype).

Ce module est **désactivé par défaut** : il n'est utilisé que si la variable
d'environnement ``MARKDOWN_CONVERTER_UI`` vaut ``qt``. PLO-34 a posé le
squelette ; PLO-35 a livré la file et le worker ; PLO-36 garnit la **toolbar**
(chips, recherche) et renforce le **bandeau de sortie** (validation écriture)
ainsi que le bouton **Vider** sur la file. PLO-37 livre le **journal** bas
(filtres niveau, lien vers ``run.log``). Le rendu reste volontairement sobre
(mockup fonctionnel) ; le polish visuel arrive avec PLO-28 et les tickets
suivants.

Architecture cible (cf. ``design_handoff_ui_refonte/README.md``) ::

    ┌──── titlebar (pastille Pandoc, toggle thème) ─────────────┐
    │ toolbar (boutons + filtres + recherche)                   │
    │ ┌── bandeau dossier de sortie ─────────────────────────┐  │
    │ │                                                      │  │
    │ │  panneau central : file de conversion │ inspecteur  │  │
    │ │                                                      │  │
    │ └──────────────────────────────────────────────────────┘  │
    │ footer (progress globale, ETA, compteurs, Convertir)      │
    │ journal repliable (caché par défaut)                      │
    └───────────────────────────────────────────────────────────┘

Tous les ``QWidget`` créés ici sont exposés comme attributs publics nommés
``_titlebar``, ``_toolbar_area``, ``_output_banner``, ``_file_view``,
``_inspector``, ``_footer`` et ``_journal`` pour permettre aux sous-tickets
suivants de les remplir sans toucher au layout global.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtCore import QThread
    from PySide6.QtWidgets import (
        QLabel,
        QLineEdit,
        QMainWindow,
        QPushButton,
        QSplitter,
        QTableView,
        QWidget,
    )

    from ui_qt_conversion_worker import ConversionWorker
    from ui_qt_file_model import ConversionFileTableModel
    from ui_qt_file_proxy import ConversionFileFilterProxy
    from ui_qt_inspector import MarkdownInspectorPanel
    from ui_qt_journal import ConversionJournalPanel


WINDOW_TITLE = "Markdown Converter"
DEFAULT_WIDTH = 1100
DEFAULT_HEIGHT = 720
INSPECTOR_INITIAL_WIDTH = 380
FILE_ROW_HEIGHT = 50  # cf. design_handoff_ui_refonte/README.md


def _validate_output_dir(path: Path) -> tuple[bool, str]:
    """Vérifie qu'un dossier de sortie est utilisable (existe, dossier, écriture)."""
    if not path.exists():
        return False, "Le dossier n'existe pas."
    if not path.is_dir():
        return False, "Le chemin désigné n'est pas un dossier."
    if not os.access(path, os.W_OK):
        return False, "Ce dossier n'est pas accessible en écriture."
    return True, ""


@dataclass
class QtZones:
    """Conteneur typé des zones de la fenêtre principale.

    Préférable à des attributs dynamiques sur ``QMainWindow`` : Pyright / Pylance
    voient les champs, et les sous-tickets PLO-35..PLO-39 ont une cible claire à
    remplir (``app.zones.toolbar_area``, ``app.zones.file_view``…).
    """

    titlebar: QWidget
    toolbar_area: QWidget
    output_banner: QWidget
    file_view: QWidget
    inspector: QWidget
    footer: QWidget
    journal: QWidget


@dataclass
class FileViewParts:
    """Sous-widgets exposés du panneau gauche (file de conversion, PLO-35/36)."""

    table: QTableView
    model: ConversionFileTableModel
    proxy: ConversionFileFilterProxy
    add_file_button: QWidget
    add_folder_button: QWidget
    clear_button: QWidget


@dataclass
class ToolbarParts:
    """Toolbar Qt (PLO-36) : champ de recherche + chips de filtre par extension."""

    search_input: QLineEdit
    chip_buttons: dict[str, QPushButton]


@dataclass
class OutputBannerParts:
    """Sous-widgets du bandeau « dossier de sortie » (PLO-35/36)."""

    label: QLabel
    choose_button: QPushButton
    error_label: QLabel


@dataclass
class FooterParts:
    """Sous-widgets du footer minimal (PLO-35) ; bouton journal (PLO-37)."""

    journal_toggle_button: QPushButton
    convert_button: QPushButton
    status_label: QLabel


class MarkdownConverterQtApp:
    """Squelette de la fenêtre principale PySide6.

    Cette classe ne hérite **pas** de ``QMainWindow`` ; elle l'agrège. Cela
    permet de l'instancier dans un contexte sans ``QApplication`` actif
    (ex. tests d'import) en différant la construction Qt à ``build()``.

    Une fois ``build()`` appelé, les widgets clés sont accessibles via
    ``self.zones`` (cf. :class:`QtZones`).
    """

    def __init__(self) -> None:
        self._window: QMainWindow | None = None
        self._central_splitter: QSplitter | None = None
        self.zones: QtZones | None = None
        self.file_view_parts: FileViewParts | None = None
        self.toolbar_parts: ToolbarParts | None = None
        self.output_banner_parts: OutputBannerParts | None = None
        self.footer_parts: FooterParts | None = None
        self.journal_panel: ConversionJournalPanel | None = None
        self.inspector_panel: MarkdownInspectorPanel | None = None
        self.output_dir: Path | None = None
        self._worker: ConversionWorker | None = None
        self._worker_thread: QThread | None = None

    def build(self) -> QMainWindow:
        """Construit et retourne la ``QMainWindow``. Ne l'affiche pas."""
        # Import local : permet d'importer ce module sans PySide6 (cf. main.py
        # qui vérifie la présence de Qt avant d'appeler ``build()``).
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QMainWindow,
            QSizePolicy,
            QSplitter,
            QVBoxLayout,
            QWidget,
        )

        window = QMainWindow()
        window.setWindowTitle(WINDOW_TITLE)
        window.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        root = QWidget(window)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        titlebar = _named_placeholder("titlebar", "Markdown Converter")
        output_banner, output_banner_parts = _build_output_banner()

        central = QSplitter(Qt.Orientation.Horizontal, root)
        file_view, file_view_parts = _build_file_view()
        toolbar_area, toolbar_parts = _build_toolbar(file_view_parts.model)
        from ui_qt_inspector import MarkdownInspectorPanel

        inspector = MarkdownInspectorPanel()
        central.addWidget(file_view)
        central.addWidget(inspector)
        central.setStretchFactor(0, 1)
        central.setStretchFactor(1, 0)
        central.setSizes([DEFAULT_WIDTH - INSPECTOR_INITIAL_WIDTH, INSPECTOR_INITIAL_WIDTH])
        central.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        footer, footer_parts = _build_footer()
        from ui_qt_journal import ConversionJournalPanel

        journal_panel = ConversionJournalPanel()
        journal_panel.setVisible(False)
        journal = journal_panel

        for w in (titlebar, toolbar_area, output_banner):
            root_layout.addWidget(w)
        root_layout.addWidget(central, stretch=1)
        for w in (footer, journal):
            root_layout.addWidget(w)

        window.setCentralWidget(root)

        self.zones = QtZones(
            titlebar=titlebar,
            toolbar_area=toolbar_area,
            output_banner=output_banner,
            file_view=file_view,
            inspector=inspector,
            footer=footer,
            journal=journal,
        )
        self._window = window
        self._central_splitter = central
        self.file_view_parts = file_view_parts
        self.toolbar_parts = toolbar_parts
        self.output_banner_parts = output_banner_parts
        self.footer_parts = footer_parts
        self.journal_panel = journal_panel
        self.inspector_panel = inspector

        output_banner_parts.choose_button.clicked.connect(self._on_choose_output_dir)
        footer_parts.journal_toggle_button.toggled.connect(journal_panel.setVisible)
        footer_parts.convert_button.clicked.connect(self._on_convert_clicked)
        footer_parts.convert_button.setEnabled(False)
        file_view_parts.clear_button.clicked.connect(self._on_clear_file_list)

        # Le bouton Convertir s'active / se désactive en fonction du contenu de
        # la file et de la sélection d'un dossier de sortie.
        file_view_parts.model.rowsInserted.connect(self._refresh_convert_button_state)
        file_view_parts.model.rowsRemoved.connect(self._refresh_convert_button_state)
        file_view_parts.model.modelReset.connect(self._refresh_convert_button_state)

        _wire_toolbar(toolbar_parts, file_view_parts)
        _wire_inspector_selection(file_view_parts, inspector)
        inspector.set_file_model(file_view_parts.model)
        # Si le modèle se réinitialise (fin de lot, vider…), on remet l'aperçu à zéro.
        file_view_parts.model.modelReset.connect(self._reset_inspector_selection)

        return window

    def set_output_dir(self, output_dir: Path) -> None:
        """Sélectionne le dossier de sortie après validation (existence + écriture)."""
        resolved = output_dir.resolve()
        ok, err = _validate_output_dir(resolved)
        if self.output_banner_parts is not None:
            if not ok:
                self.output_banner_parts.error_label.setText(err)
                self.output_banner_parts.error_label.setVisible(True)
                self.output_banner_parts.error_label.show()
                return
            self.output_banner_parts.error_label.clear()
            self.output_banner_parts.error_label.setVisible(False)
            self.output_banner_parts.label.setText(f"Dossier de sortie : {resolved}")
        self.output_dir = resolved
        self._refresh_convert_button_state()

    def _on_clear_file_list(self) -> None:
        if self.file_view_parts is None or self.toolbar_parts is None:
            return
        model = self.file_view_parts.model
        if not model.records():
            return
        from PySide6.QtWidgets import QMessageBox

        n = len(model.records())
        reply = QMessageBox.question(
            self._window,
            "Vider la file",
            f"Voulez-vous retirer les {n} fichier(s) de la file ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        model.clear()
        self.toolbar_parts.search_input.blockSignals(True)
        self.toolbar_parts.search_input.clear()
        self.toolbar_parts.search_input.blockSignals(False)
        for btn in self.toolbar_parts.chip_buttons.values():
            btn.blockSignals(True)
            btn.setChecked(False)
            btn.blockSignals(False)
        self.file_view_parts.proxy.set_active_extensions(set())
        self.file_view_parts.proxy.set_name_filter("")

    def _refresh_convert_button_state(self, *_: object) -> None:
        if self.footer_parts is None or self.file_view_parts is None:
            return
        ready = self.output_dir is not None and bool(self.file_view_parts.model.records())
        running = self._worker_thread is not None
        self.footer_parts.convert_button.setEnabled(ready and not running)

    def _on_choose_output_dir(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        folder_str = QFileDialog.getExistingDirectory(self._window, "Choisir le dossier de sortie")
        if folder_str:
            self.set_output_dir(Path(folder_str))

    def _on_convert_clicked(self) -> None:
        if self.output_dir is None or self.file_view_parts is None or self.footer_parts is None:
            return
        from PySide6.QtCore import Qt, QThread

        from ui_qt_conversion_worker import ConversionWorker

        paths = [rec.source_path for rec in self.file_view_parts.model.records()]
        if not paths:
            return

        worker = ConversionWorker(
            explicit_files=paths,
            directory_roots=[],
            output_dir=self.output_dir,
            keep_output_in_memory=True,
        )
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        if self.journal_panel is not None:
            worker.log.connect(
                self.journal_panel.append_log,
                Qt.ConnectionType.QueuedConnection,
            )
        worker.progress.connect(self._on_worker_progress)
        worker.finished.connect(self._on_worker_finished)
        worker.failed.connect(self._on_worker_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_worker_refs)

        self._worker = worker
        self._worker_thread = thread
        self.footer_parts.convert_button.setEnabled(False)
        self.footer_parts.status_label.setText("Conversion en cours…")
        thread.start()

    def _on_worker_progress(self, index: int, total: int, label: str, percent: float) -> None:
        if self.file_view_parts is None or self.footer_parts is None:
            return
        records = self.file_view_parts.model.records()
        if total <= 0 or not records:
            return
        from converter import ConversionStatus

        row = index if index < len(records) else len(records) - 1
        rec = records[row]
        rec.progress_percent = max(0.0, min(1.0, percent * total - row))
        if rec.status == ConversionStatus.QUEUED:
            rec.status = ConversionStatus.PROCESSING
        self.file_view_parts.model.refresh_row(row)
        self.footer_parts.status_label.setText(
            f"Conversion en cours… {label} ({round(percent * 100)} %)"
        )

    def _on_worker_finished(self, summary: object) -> None:
        if self.file_view_parts is None or self.footer_parts is None:
            return
        from converter import ConversionStatus, ConversionSummary

        if not isinstance(summary, ConversionSummary):
            return
        self.file_view_parts.model.set_records(list(summary.records))
        errors = sum(1 for r in summary.records if r.status == ConversionStatus.ERROR)
        self.footer_parts.status_label.setText(
            f"Terminé · {len(summary.records)} fichier(s), {errors} erreur(s)."
        )
        self._refresh_convert_button_state()

    def _on_worker_failed(self, error_text: str) -> None:
        if self.footer_parts is None:
            return
        first_line = error_text.splitlines()[0] if error_text else "Échec de la conversion."
        self.footer_parts.status_label.setText(f"Échec : {first_line}")
        self._refresh_convert_button_state()

    def _clear_worker_refs(self) -> None:
        self._worker = None
        self._worker_thread = None
        self._refresh_convert_button_state()

    def _reset_inspector_selection(self) -> None:
        if self.inspector_panel is not None:
            self.inspector_panel.set_record(None)


def _named_placeholder(name: str, text: str) -> QWidget:
    """Crée un placeholder visuel discret avec un ``objectName`` pour le retrouver."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

    frame = QFrame()
    frame.setObjectName(name)
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(12, 8, 12, 8)
    label = QLabel(text, frame)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(label, stretch=1)
    return frame


def _build_output_banner() -> tuple[QWidget, OutputBannerParts]:
    """Bandeau « Dossier de sortie » : libellé, erreur éventuelle, bouton ``Choisir…``."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

    frame = QFrame()
    frame.setObjectName("output_banner")
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    frame.setMinimumHeight(72)
    outer = QVBoxLayout(frame)
    outer.setContentsMargins(12, 10, 12, 10)
    outer.setSpacing(4)
    row = QHBoxLayout()
    row.setSpacing(8)
    label = QLabel("Dossier de sortie : —", frame)
    label.setObjectName("output_banner_label")
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    button = QPushButton("Choisir…", frame)
    button.setObjectName("output_banner_choose")
    button.setToolTip(
        "Choisir un dossier existant où seront écrits les fichiers Markdown. "
        "Le programme vérifie que vous avez le droit d'y écrire."
    )
    row.addWidget(label, stretch=1)
    row.addWidget(button)
    outer.addLayout(row)
    error_label = QLabel("", frame)
    error_label.setObjectName("output_banner_error")
    error_label.setWordWrap(True)
    error_label.setVisible(False)
    error_label.setStyleSheet("color: #b00020;")
    outer.addWidget(error_label)
    return frame, OutputBannerParts(label=label, choose_button=button, error_label=error_label)


def _build_footer() -> tuple[QWidget, FooterParts]:
    """Footer minimal (PLO-35) : statut + journal (PLO-37) + **Convertir**."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

    frame = QFrame()
    frame.setObjectName("footer")
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(12, 8, 12, 8)
    layout.setSpacing(8)
    status = QLabel("Prêt.", frame)
    status.setObjectName("footer_status")
    status.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    journal_toggle = QPushButton("Journal", frame)
    journal_toggle.setObjectName("footer_journal_toggle")
    journal_toggle.setCheckable(True)
    journal_toggle.setToolTip("Afficher ou masquer le journal de conversion.")
    convert = QPushButton("Convertir", frame)
    convert.setObjectName("footer_convert")
    convert.setDefault(True)
    layout.addWidget(status, stretch=1)
    layout.addWidget(journal_toggle)
    layout.addWidget(convert)
    return frame, FooterParts(
        journal_toggle_button=journal_toggle,
        convert_button=convert,
        status_label=status,
    )


def _build_file_view() -> tuple[QWidget, FileViewParts]:
    """Construit la zone gauche : mini-toolbar (Fichier / Dossier) + ``QTableView``.

    La table consomme un ``ConversionFileFilterProxy`` qui enveloppe le modèle
    source — les chips et la recherche de la toolbar (PLO-36) modifient ce
    proxy sans toucher au modèle.
    """
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QHeaderView,
        QPushButton,
        QSizePolicy,
        QTableView,
        QVBoxLayout,
    )

    from ui_qt_file_model import ConversionFileTableModel
    from ui_qt_file_proxy import ConversionFileFilterProxy

    frame = QFrame()
    frame.setObjectName("file_view")
    frame.setFrameShape(QFrame.Shape.StyledPanel)

    root_layout = QVBoxLayout(frame)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)

    toolbar = QFrame(frame)
    toolbar.setObjectName("file_view_toolbar")
    toolbar_layout = QHBoxLayout(toolbar)
    toolbar_layout.setContentsMargins(12, 8, 12, 8)
    toolbar_layout.setSpacing(8)
    add_file_btn = QPushButton("+ Fichiers", toolbar)
    add_file_btn.setObjectName("file_view_add_file")
    add_folder_btn = QPushButton("Dossier…", toolbar)
    add_folder_btn.setObjectName("file_view_add_folder")
    clear_btn = QPushButton("Vider", toolbar)
    clear_btn.setObjectName("file_view_clear")
    clear_btn.setToolTip("Retirer tous les fichiers de la file (demande confirmation).")
    toolbar_layout.addWidget(add_file_btn)
    toolbar_layout.addWidget(add_folder_btn)
    toolbar_layout.addWidget(clear_btn)
    toolbar_layout.addStretch(1)

    model = ConversionFileTableModel()
    proxy = ConversionFileFilterProxy(model)
    table = QTableView(frame)
    table.setObjectName("file_view_table")
    table.setModel(proxy)
    table.setSortingEnabled(True)
    table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(FILE_ROW_HEIGHT)
    table.horizontalHeader().setStretchLastSection(False)
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    for col in (2, 3, 4):
        table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
    table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    root_layout.addWidget(toolbar)
    root_layout.addWidget(table, stretch=1)

    add_file_btn.clicked.connect(lambda: _on_add_files_clicked(frame, model))
    add_folder_btn.clicked.connect(lambda: _on_add_folder_clicked(frame, model))

    return frame, FileViewParts(
        table=table,
        model=model,
        proxy=proxy,
        add_file_button=add_file_btn,
        add_folder_button=add_folder_btn,
        clear_button=clear_btn,
    )


# Ordre stable des chips dans la toolbar. On garde l'ordre d'apparition naturelle
# dans le design handoff (du plus fréquent au moins fréquent côté usage).
_CHIP_EXTENSIONS: tuple[str, ...] = (".docx", ".pdf", ".pptx", ".xlsx", ".html", ".txt")


def _build_toolbar(source_model: ConversionFileTableModel) -> tuple[QWidget, ToolbarParts]:
    """Toolbar : chips de filtre par extension (avec compteurs) + champ de recherche."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QPalette
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLineEdit,
        QPushButton,
        QSizePolicy,
    )

    from ui_qt_file_model import format_accent_hex

    frame = QFrame()
    frame.setObjectName("toolbar")
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(12, 8, 12, 8)
    layout.setSpacing(8)

    chip_buttons: dict[str, QPushButton] = {}
    for ext in _CHIP_EXTENSIONS:
        btn = QPushButton(_chip_label(ext, 0), frame)
        btn.setObjectName(f"toolbar_chip_{ext.lstrip('.')}")
        btn.setCheckable(True)
        btn.setAutoExclusive(False)
        btn.setToolTip(f"Filtrer la file pour ne montrer que les {ext}")
        accent = QColor(format_accent_hex(ext))
        palette = btn.palette()
        palette.setColor(QPalette.ColorRole.Button, accent)
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
        btn.setPalette(palette)
        layout.addWidget(btn)
        chip_buttons[ext] = btn

    layout.addStretch(1)

    search = QLineEdit(frame)
    search.setObjectName("toolbar_search")
    search.setPlaceholderText("Rechercher un fichier…")
    search.setClearButtonEnabled(True)
    search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    search.setMinimumWidth(240)
    search.setMaximumWidth(360)
    layout.addWidget(search)
    _ = Qt  # silencieux : import gardé pour les variantes futures

    parts = ToolbarParts(search_input=search, chip_buttons=chip_buttons)
    _refresh_chip_counters(parts, source_model)
    source_model.rowsInserted.connect(lambda *_: _refresh_chip_counters(parts, source_model))
    source_model.rowsRemoved.connect(lambda *_: _refresh_chip_counters(parts, source_model))
    source_model.modelReset.connect(lambda: _refresh_chip_counters(parts, source_model))
    return frame, parts


def _wire_toolbar(toolbar_parts: ToolbarParts, file_view_parts: FileViewParts) -> None:
    """Connecte chips et recherche au proxy."""
    proxy = file_view_parts.proxy

    def _apply_active_extensions() -> None:
        active = {ext for ext, btn in toolbar_parts.chip_buttons.items() if btn.isChecked()}
        proxy.set_active_extensions(active)

    for btn in toolbar_parts.chip_buttons.values():
        btn.toggled.connect(lambda _checked=False: _apply_active_extensions())

    toolbar_parts.search_input.textChanged.connect(proxy.set_name_filter)


def _wire_inspector_selection(
    file_view_parts: FileViewParts,
    inspector: MarkdownInspectorPanel,
) -> None:
    """Synchronise la sélection courante de la file avec l'inspecteur."""
    from PySide6.QtCore import QModelIndex

    selection_model = file_view_parts.table.selectionModel()
    if selection_model is None:
        return

    def _on_current_row_changed(current: QModelIndex, _previous: QModelIndex) -> None:
        if not current.isValid():
            inspector.set_record(None)
            return
        rec = file_view_parts.proxy.source_record_at(current.row())
        from converter import FileConversionRecord as _Record

        inspector.set_record(rec if isinstance(rec, _Record) else None)

    selection_model.currentRowChanged.connect(_on_current_row_changed)


def _chip_label(ext: str, count: int) -> str:
    return f"{ext}  {count}"


def _refresh_chip_counters(parts: ToolbarParts, source_model: ConversionFileTableModel) -> None:
    """Recompte les fichiers par extension sur le **modèle source** (pas le proxy)."""
    from utils import normalize_extension

    counts: dict[str, int] = {ext: 0 for ext in parts.chip_buttons}
    for rec in source_model.records():
        ext = normalize_extension(rec.source_path)
        if ext in counts:
            counts[ext] += 1
    for ext, btn in parts.chip_buttons.items():
        btn.setText(_chip_label(ext, counts[ext]))


def _on_add_files_clicked(parent: QWidget, model: ConversionFileTableModel) -> None:
    from PySide6.QtWidgets import QFileDialog

    from utils import SUPPORTED_EXTENSIONS

    pattern = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))
    paths_str, _ = QFileDialog.getOpenFileNames(
        parent,
        "Ajouter des fichiers",
        "",
        f"Fichiers pris en charge ({pattern});;Tous les fichiers (*)",
    )
    add_paths_to_model(model, [Path(p) for p in paths_str])


def _on_add_folder_clicked(parent: QWidget, model: ConversionFileTableModel) -> None:
    from PySide6.QtWidgets import QFileDialog

    folder_str = QFileDialog.getExistingDirectory(parent, "Ajouter un dossier")
    if not folder_str:
        return
    from utils import collect_supported_files_under_directory

    add_paths_to_model(model, collect_supported_files_under_directory(Path(folder_str)))


def add_paths_to_model(model: ConversionFileTableModel, paths: list[Path]) -> list[Path]:
    """Ajoute les chemins inconnus à ``model`` en statut ``QUEUED``.

    Retourne la liste des chemins effectivement ajoutés (utile pour les tests
    et pour un futur message footer).
    """
    from converter import ConversionStatus, FileConversionRecord
    from utils import is_supported_path

    existing = {rec.source_path.resolve() for rec in model.records()}
    added: list[Path] = []
    for p in paths:
        rp = p.resolve()
        if rp in existing or not is_supported_path(rp):
            continue
        model.append_record(
            FileConversionRecord(
                source_path=rp,
                status=ConversionStatus.QUEUED,
            )
        )
        existing.add(rp)
        added.append(rp)
    return added


def run_app() -> None:
    """Lance la boucle Qt.

    Conçu pour être appelé depuis ``main.py`` à la place de ``ui.run_app``
    quand ``MARKDOWN_CONVERTER_UI=qt``.

    Important : on garde une référence locale forte à ``qt_app``. PySide6
    connecte les bound methods via une **référence faible** ; sans cette
    variable, le GC peut libérer l'instance dès la sortie de cette fonction
    locale et invalider silencieusement les slots (boutons qui ne réagissent
    plus, etc.). Conserver ``qt_app`` jusqu'à la fin de ``app.exec()``
    garantit que les slots restent appelables.
    """
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    qt_app = MarkdownConverterQtApp()
    window = qt_app.build()
    window.show()
    exit_code = app.exec()
    del qt_app  # explicite : la référence ne sert plus une fois exec() rendu
    sys.exit(exit_code)
