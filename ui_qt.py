"""
Interface PySide6 du Markdown Converter (prototype, bootstrap).

Ce module est **désactivé par défaut** : il n'est utilisé que si la variable
d'environnement ``MARKDOWN_CONVERTER_UI`` vaut ``qt``. À ce stade (PLO-34),
on pose uniquement le squelette : fenêtre principale, zones nommées, aucune
logique fonctionnelle. Les widgets seront garnis dans les sous-tickets
suivants (file de conversion, toolbar, inspecteur, footer, journal).

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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget


WINDOW_TITLE = "Markdown Converter"
DEFAULT_WIDTH = 1100
DEFAULT_HEIGHT = 720
INSPECTOR_INITIAL_WIDTH = 380


class MarkdownConverterQtApp:
    """Squelette de la fenêtre principale PySide6.

    Cette classe ne hérite **pas** de ``QMainWindow`` ; elle l'agrège. Cela
    permet de l'instancier dans un contexte sans ``QApplication`` actif
    (ex. tests d'import) en différant la construction Qt à ``build()``.
    """

    def __init__(self) -> None:
        self._window: QMainWindow | None = None
        self._central_splitter: QSplitter | None = None

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
        file_view = _named_placeholder("file_view", "File de conversion (sous-ticket #2)")
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

        window._titlebar = titlebar
        window._toolbar_area = toolbar_area
        window._output_banner = output_banner
        window._file_view = file_view
        window._inspector = inspector
        window._footer = footer
        window._journal = journal

        self._window = window
        self._central_splitter = central
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
