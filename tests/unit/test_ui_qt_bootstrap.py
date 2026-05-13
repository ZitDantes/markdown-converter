"""
Smoke tests du squelette ``ui_qt`` (PLO-34).

Deux propriétés essentielles à protéger sur la durée :

1. ``import ui_qt`` fonctionne **même** sans PySide6 installé (les imports
   Qt sont locaux aux méthodes ``build()`` / ``run_app()``). C'est ce qui
   permet à ``main.py`` de tomber proprement en fallback Tk si Qt manque.
2. Quand PySide6 est présent, ``MarkdownConverterQtApp().build()`` crée une
   ``QMainWindow`` à zones nommées (titlebar / toolbar / inspector / footer
   / journal), avec le journal caché par défaut.

Le test (2) est skip si PySide6 n'est pas installé sur la machine de test.
"""

from __future__ import annotations

import pytest


def test_import_ui_qt_without_pyside6_does_not_fail() -> None:
    """``import ui_qt`` n'exécute aucun code PySide6 — il doit toujours réussir."""
    import importlib

    module = importlib.import_module("ui_qt")
    assert hasattr(module, "MarkdownConverterQtApp")
    assert hasattr(module, "run_app")


pyside6 = pytest.importorskip("PySide6", reason="PySide6 non installé localement")


@pytest.fixture
def qt_app() -> object:
    """``QApplication`` partagée en mode offscreen pour ce module de tests."""
    import os
    import sys

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def test_build_creates_named_zones(qt_app: object) -> None:
    from ui_qt import MarkdownConverterQtApp

    window = MarkdownConverterQtApp().build()
    assert window.windowTitle() == "Markdown Converter"

    for attr in (
        "_titlebar",
        "_toolbar_area",
        "_output_banner",
        "_file_view",
        "_inspector",
        "_footer",
        "_journal",
    ):
        zone = getattr(window, attr)
        assert zone is not None, f"zone {attr} manquante"
        assert zone.objectName(), f"zone {attr} doit avoir un objectName"


def test_journal_is_hidden_by_default(qt_app: object) -> None:
    from ui_qt import MarkdownConverterQtApp

    window = MarkdownConverterQtApp().build()
    assert window._journal.isVisible() is False
