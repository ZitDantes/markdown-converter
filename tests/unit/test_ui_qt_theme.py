"""Smoke tests thème Qt (PLO-28)."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("PySide6")


@pytest.fixture
def qt_app() -> object:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_apply_qt_theme_light_and_dark(qt_app: object) -> None:
    from PySide6.QtWidgets import QApplication, QMainWindow

    from ui_qt_theme import apply_qt_theme

    win = QMainWindow()
    app = QApplication.instance()
    assert app is not None
    apply_qt_theme(app, win, "dark")
    apply_qt_theme(app, win, "light")
