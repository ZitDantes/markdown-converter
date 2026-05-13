"""
Interface PySide6 du Markdown Converter (prototype).

Ce module est **désactivé par défaut** : il n'est utilisé que si la variable
d'environnement ``MARKDOWN_CONVERTER_UI`` vaut ``qt``. PLO-34 a posé le
squelette ; PLO-35 garnit la zone ``file_view`` avec la **file de conversion**
(``QTableView`` branchée sur ``ConversionFileTableModel``) et deux boutons
minimalistes d'ajout de sources. Les autres zones (toolbar, inspecteur,
footer, journal) restent des placeholders jusqu'à PLO-36..PLO-39.

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


WINDOW_TITLE = "Markdown Converter"
DEFAULT_WIDTH = 1100
DEFAULT_HEIGHT = 720
INSPECTOR_INITIAL_WIDTH = 380
FILE_ROW_HEIGHT = 50  # cf. design_handoff_ui_refonte/README.md


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


@dataclass
class ToolbarParts:
    """Toolbar Qt (PLO-36) : champ de recherche + chips de filtre par extension."""

    search_input: QLineEdit
    chip_buttons: dict[str, QPushButton]


@dataclass
class OutputBannerParts:
    """Sous-widgets du bandeau « dossier de sortie » (PLO-35, minimal)."""

    label: QLabel
    choose_button: QPushButton


@dataclass
class FooterParts:
    """Sous-widgets du footer minimal (PLO-35) ; sera enrichi en PLO-38."""

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
        inspector = _named_placeholder("inspector", "Inspecteur (sous-ticket #4)")
        central.addWidget(file_view)
        central.addWidget(inspector)
        central.setStretchFactor(0, 1)
        central.setStretchFactor(1, 0)
        central.setSizes([DEFAULT_WIDTH - INSPECTOR_INITIAL_WIDTH, INSPECTOR_INITIAL_WIDTH])
        central.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        footer, footer_parts = _build_footer()
        journal = _named_placeholder("journal", "Journal (sous-ticket #6) — caché par défaut")
        journal.setVisible(False)

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

        output_banner_parts.choose_button.clicked.connect(self._on_choose_output_dir)
        footer_parts.convert_button.clicked.connect(self._on_convert_clicked)
        footer_parts.convert_button.setEnabled(False)

        # Le bouton Convertir s'active / se désactive en fonction du contenu de
        # la file et de la sélection d'un dossier de sortie.
        file_view_parts.model.rowsInserted.connect(self._refresh_convert_button_state)
        file_view_parts.model.rowsRemoved.connect(self._refresh_convert_button_state)
        file_view_parts.model.modelReset.connect(self._refresh_convert_button_state)

        _wire_toolbar(toolbar_parts, file_view_parts)

        return window

    def set_output_dir(self, output_dir: Path) -> None:
        """Sélectionne le dossier de sortie. Met à jour le bandeau et le bouton Convertir."""
        self.output_dir = output_dir.resolve()
        if self.output_banner_parts is not None:
            self.output_banner_parts.label.setText(f"Dossier de sortie : {self.output_dir}")
        self._refresh_convert_button_state()

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
        from PySide6.QtCore import QThread

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
    """Bandeau « Dossier de sortie » minimal (PLO-35) avec un bouton ``Choisir…``."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

    frame = QFrame()
    frame.setObjectName("output_banner")
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(12, 8, 12, 8)
    layout.setSpacing(8)
    label = QLabel("Dossier de sortie : —", frame)
    label.setObjectName("output_banner_label")
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    button = QPushButton("Choisir…", frame)
    button.setObjectName("output_banner_choose")
    layout.addWidget(label, stretch=1)
    layout.addWidget(button)
    return frame, OutputBannerParts(label=label, choose_button=button)


def _build_footer() -> tuple[QWidget, FooterParts]:
    """Footer minimal (PLO-35) : statut + bouton **Convertir** primaire."""
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
    convert = QPushButton("Convertir", frame)
    convert.setObjectName("footer_convert")
    convert.setDefault(True)
    layout.addWidget(status, stretch=1)
    layout.addWidget(convert)
    return frame, FooterParts(convert_button=convert, status_label=status)


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
    toolbar_layout.addWidget(add_file_btn)
    toolbar_layout.addWidget(add_folder_btn)
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
