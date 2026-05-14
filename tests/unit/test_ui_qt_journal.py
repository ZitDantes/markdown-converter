"""
Tests du journal Qt (PLO-37).
"""

from __future__ import annotations

import sys

import pytest


@pytest.fixture
def qt_app() -> object:
    pytest.importorskip("PySide6", reason="PySide6 non installé localement")
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def test_journal_panel_object_name(qt_app: object) -> None:
    from ui_qt_journal import ConversionJournalPanel

    panel = ConversionJournalPanel()
    assert panel.objectName() == "conversion_journal"


def test_build_exposes_journal_panel(qt_app: object) -> None:
    from ui_qt import MarkdownConverterQtApp
    from ui_qt_journal import ConversionJournalPanel

    app = MarkdownConverterQtApp()
    app.build()
    assert isinstance(app.journal_panel, ConversionJournalPanel)
    assert app.zones is not None
    assert app.zones.journal is app.journal_panel


def test_journal_hidden_toggle_in_footer(qt_app: object) -> None:
    from ui_qt import MarkdownConverterQtApp

    app = MarkdownConverterQtApp()
    app.build()
    assert app.journal_panel is not None
    assert app.footer_parts is not None
    # ``isVisible()`` dépend de la hiérarchie affichée ; ``isHidden()`` reflète
    # le masquage explicite (fenêtre non ``show()`` en test).
    assert app.journal_panel.isHidden() is True
    assert app.footer_parts.journal_toggle_button.isChecked() is False

    app.footer_parts.journal_toggle_button.setChecked(True)
    assert app.journal_panel.isHidden() is False

    app.footer_parts.journal_toggle_button.setChecked(False)
    assert app.journal_panel.isHidden() is True


def test_append_updates_counters_and_plain_text(qt_app: object) -> None:
    from ui_qt_journal import ConversionJournalPanel

    panel = ConversionJournalPanel()
    panel.append_log("INFO", "ligne info")
    panel.append_log("WARNING", "ligne warn")
    assert "Tout (2)" in panel._btn_all.text()
    assert "Info (1)" in panel._btn_info.text()
    assert "Warn (1)" in panel._btn_warn.text()
    plain = panel._text.toPlainText()
    assert "[INFO]" in plain
    assert "ligne info" in plain
    assert "[WARN]" in plain
    assert "ligne warn" in plain


def test_filter_warn_hides_info_lines(qt_app: object) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    from ui_qt_journal import ConversionJournalPanel

    panel = ConversionJournalPanel()
    panel.append_log("INFO", "un")
    panel.append_log("WARNING", "deux")
    QTest.mouseClick(panel._btn_warn, Qt.MouseButton.LeftButton)
    plain = panel._text.toPlainText()
    assert "deux" in plain
    assert "un" not in plain


def test_filter_change_rebuilds_from_memory(qt_app: object) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    from ui_qt_journal import ConversionJournalPanel

    panel = ConversionJournalPanel()
    panel.append_log("INFO", "cache")
    QTest.mouseClick(panel._btn_info, Qt.MouseButton.LeftButton)
    assert "cache" in panel._text.toPlainText()
    panel.append_log("WARNING", "alerte")
    # Filtre Info : le WARN n'apparaît pas tant qu'on ne change pas de filtre.
    assert "alerte" not in panel._text.toPlainText()
    QTest.mouseClick(panel._btn_all, Qt.MouseButton.LeftButton)
    plain = panel._text.toPlainText()
    assert "cache" in plain
    assert "alerte" in plain


def test_open_log_link_calls_desktop_services(
    qt_app: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtCore import QUrl

    from ui_qt_journal import ConversionJournalPanel

    opened: list[object] = []

    def fake_open(url: object) -> bool:
        opened.append(url)
        return True

    monkeypatch.setattr("ui_qt_journal.QDesktopServices.openUrl", fake_open)
    panel = ConversionJournalPanel()
    panel._on_open_log_link("openlog")
    assert len(opened) == 1
    assert isinstance(opened[0], QUrl)
    assert opened[0].isLocalFile()
