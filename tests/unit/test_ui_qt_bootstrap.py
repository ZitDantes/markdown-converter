"""
Smoke tests du squelette ``ui_qt`` (PLO-34).

Deux propriétés essentielles à protéger sur la durée :

1. ``import ui_qt`` fonctionne **même** sans PySide6 installé (les imports
   Qt sont locaux aux méthodes ``build()`` / ``run_app()``). C'est ce qui
   permet à ``main.py`` de tomber proprement en fallback Tk si Qt manque.
   Ce test reste collecté **et exécuté** quoi qu'il arrive ; il ne doit
   dépendre d'aucune fixture liée à PySide6.
2. Quand PySide6 est présent, ``MarkdownConverterQtApp().build()`` crée une
   ``QMainWindow`` à zones nommées et le journal y est caché par défaut.
   Ces tests utilisent la fixture ``qt_app`` qui appelle
   ``pytest.importorskip("PySide6")`` — donc skip individuellement, sans
   sauter aussi le test (1).
"""

from __future__ import annotations

import pytest


def test_import_ui_qt_without_pyside6_does_not_fail() -> None:
    """``import ui_qt`` n'exécute aucun code PySide6 — il doit toujours réussir."""
    import importlib

    module = importlib.import_module("ui_qt")
    assert hasattr(module, "MarkdownConverterQtApp")
    assert hasattr(module, "QtZones")
    assert hasattr(module, "run_app")


@pytest.fixture
def qt_app() -> object:
    """``QApplication`` partagée en mode offscreen.

    ``pytest.importorskip`` est appelé **dans** la fixture : seuls les tests
    qui dépendent de cette fixture sont skip si PySide6 est absent ; le
    test 1 ci-dessus reste exécuté.
    """
    pytest.importorskip("PySide6", reason="PySide6 non installé localement")

    import os
    import sys

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def test_build_creates_named_zones(qt_app: object) -> None:
    from ui_qt import MarkdownConverterQtApp, QtZones

    app = MarkdownConverterQtApp()
    window = app.build()
    assert window.windowTitle() == "Markdown Converter"
    assert isinstance(app.zones, QtZones)

    for attr in (
        "titlebar",
        "toolbar_area",
        "output_banner",
        "file_view",
        "inspector",
        "footer",
        "journal",
    ):
        zone = getattr(app.zones, attr)
        assert zone is not None, f"zone {attr} manquante"
        assert zone.objectName(), f"zone {attr} doit avoir un objectName"


def test_journal_is_hidden_by_default(qt_app: object) -> None:
    from ui_qt import MarkdownConverterQtApp

    app = MarkdownConverterQtApp()
    app.build()
    assert app.zones is not None
    assert app.zones.journal.isVisible() is False
