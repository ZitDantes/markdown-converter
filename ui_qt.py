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
    from PySide6.QtWidgets import QMainWindow, QSplitter, QTableView, QWidget

    from ui_qt_file_model import ConversionFileTableModel


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
    """Sous-widgets exposés du panneau gauche (file de conversion, PLO-35)."""

    table: QTableView
    model: ConversionFileTableModel
    add_file_button: QWidget
    add_folder_button: QWidget


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
        toolbar_area = _named_placeholder("toolbar", "Toolbar (sous-ticket #3)")
        output_banner = _named_placeholder("output_banner", "Dossier de sortie : —")

        central = QSplitter(Qt.Orientation.Horizontal, root)
        file_view, file_view_parts = _build_file_view()
        inspector = _named_placeholder("inspector", "Inspecteur (sous-ticket #4)")
        central.addWidget(file_view)
        central.addWidget(inspector)
        central.setStretchFactor(0, 1)
        central.setStretchFactor(1, 0)
        central.setSizes([DEFAULT_WIDTH - INSPECTOR_INITIAL_WIDTH, INSPECTOR_INITIAL_WIDTH])
        central.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        footer = _named_placeholder("footer", "Footer (sous-ticket #5)")
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
        return window


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


def _build_file_view() -> tuple[QWidget, FileViewParts]:
    """Construit la zone gauche : mini-toolbar (Fichier / Dossier) + ``QTableView``.

    Le toolbar complet (recherche, chips de filtre…) viendra au sous-ticket #3.
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
    table = QTableView(frame)
    table.setObjectName("file_view_table")
    table.setModel(model)
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
        add_file_button=add_file_btn,
        add_folder_button=add_folder_btn,
    )


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
    """
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    window = MarkdownConverterQtApp().build()
    window.show()
    sys.exit(app.exec())
