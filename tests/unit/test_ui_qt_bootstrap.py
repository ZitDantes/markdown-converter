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

import sys

import pytest


def test_import_ui_qt_without_pyside6_does_not_fail() -> None:
    """``import ui_qt`` n'exécute aucun code PySide6 — il doit toujours réussir."""
    import importlib

    module = importlib.import_module("ui_qt")
    assert hasattr(module, "MarkdownConverterQtApp")
    assert hasattr(module, "QtZones")
    assert hasattr(module, "FileViewParts")
    assert hasattr(module, "add_paths_to_model")
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


def test_file_view_parts_exposed_after_build(qt_app: object) -> None:
    from ui_qt import FileViewParts, MarkdownConverterQtApp
    from ui_qt_file_model import ConversionFileTableModel
    from ui_qt_file_proxy import ConversionFileFilterProxy

    app = MarkdownConverterQtApp()
    app.build()
    parts = app.file_view_parts
    assert isinstance(parts, FileViewParts)
    assert isinstance(parts.model, ConversionFileTableModel)
    assert isinstance(parts.proxy, ConversionFileFilterProxy)
    assert parts.table.model() is parts.proxy
    assert parts.proxy.sourceModel() is parts.model
    assert parts.add_file_button.objectName() == "file_view_add_file"
    assert parts.add_folder_button.objectName() == "file_view_add_folder"
    assert parts.clear_button.objectName() == "file_view_clear"


def test_add_paths_to_model_filters_and_dedupes(qt_app: object, tmp_path: object) -> None:
    from converter import ConversionStatus
    from ui_qt import add_paths_to_model
    from ui_qt_file_model import ConversionFileTableModel

    supported = tmp_path / "doc.docx"
    supported.write_bytes(b"x")
    unsupported = tmp_path / "weird.zzz"
    unsupported.write_bytes(b"x")

    model = ConversionFileTableModel()
    added = add_paths_to_model(model, [supported, unsupported, supported])
    assert [p.name for p in added] == ["doc.docx"]
    assert len(model.records()) == 1
    assert model.records()[0].status == ConversionStatus.QUEUED

    again = add_paths_to_model(model, [supported])
    assert again == []
    assert len(model.records()) == 1


def test_convert_button_disabled_until_files_and_output(qt_app: object, tmp_path: object) -> None:
    from ui_qt import MarkdownConverterQtApp, add_paths_to_model

    app = MarkdownConverterQtApp()
    app.build()
    assert app.footer_parts is not None
    assert app.file_view_parts is not None

    assert app.footer_parts.convert_button.isEnabled() is False

    src = tmp_path / "doc.docx"
    src.write_bytes(b"x")
    add_paths_to_model(app.file_view_parts.model, [src])
    assert app.footer_parts.convert_button.isEnabled() is False

    out = tmp_path / "out"
    out.mkdir()
    app.set_output_dir(out)
    assert app.footer_parts.convert_button.isEnabled() is True


def test_set_output_dir_updates_banner(qt_app: object, tmp_path: object) -> None:
    from ui_qt import MarkdownConverterQtApp

    app = MarkdownConverterQtApp()
    app.build()
    target = tmp_path / "out"
    target.mkdir()
    app.set_output_dir(target)
    assert app.output_banner_parts is not None
    assert str(target.resolve()) in app.output_banner_parts.label.text()
    assert app.output_banner_parts.error_label.isVisible() is False


def test_toolbar_chip_filters_proxy(qt_app: object, tmp_path: object) -> None:
    from ui_qt import MarkdownConverterQtApp, add_paths_to_model

    app = MarkdownConverterQtApp()
    app.build()
    assert app.toolbar_parts is not None
    assert app.file_view_parts is not None

    docx = tmp_path / "doc.docx"
    pdf = tmp_path / "rep.pdf"
    txt = tmp_path / "notes.txt"
    for p in (docx, pdf, txt):
        p.write_bytes(b"x")
    add_paths_to_model(app.file_view_parts.model, [docx, pdf, txt])

    assert app.file_view_parts.proxy.rowCount() == 3
    assert app.toolbar_parts.chip_buttons[".docx"].text().endswith(" 1")
    assert app.toolbar_parts.chip_buttons[".pdf"].text().endswith(" 1")
    assert app.toolbar_parts.chip_buttons[".pptx"].text().endswith(" 0")

    app.toolbar_parts.chip_buttons[".pdf"].setChecked(True)
    assert app.file_view_parts.proxy.rowCount() == 1
    assert app.file_view_parts.proxy.active_extensions() == {".pdf"}

    app.toolbar_parts.chip_buttons[".pdf"].setChecked(False)
    assert app.file_view_parts.proxy.rowCount() == 3


def test_toolbar_search_filters_proxy(qt_app: object, tmp_path: object) -> None:
    from ui_qt import MarkdownConverterQtApp, add_paths_to_model

    app = MarkdownConverterQtApp()
    app.build()
    assert app.toolbar_parts is not None
    assert app.file_view_parts is not None

    a = tmp_path / "rapport.docx"
    b = tmp_path / "annexe.docx"
    for p in (a, b):
        p.write_bytes(b"x")
    add_paths_to_model(app.file_view_parts.model, [a, b])

    app.toolbar_parts.search_input.setText("RAP")
    assert app.file_view_parts.proxy.rowCount() == 1
    rec = app.file_view_parts.proxy.source_record_at(0)
    assert rec is not None
    assert rec.source_path.name == "rapport.docx"

    app.toolbar_parts.search_input.setText("")
    assert app.file_view_parts.proxy.rowCount() == 2


def test_set_output_dir_rejects_missing_directory(qt_app: object, tmp_path: object) -> None:
    from ui_qt import MarkdownConverterQtApp

    app = MarkdownConverterQtApp()
    app.build()
    ghost = tmp_path / "inexistant"
    app.set_output_dir(ghost)
    assert app.output_dir is None
    assert app.output_banner_parts is not None
    assert "n'existe pas" in app.output_banner_parts.error_label.text()


def test_set_output_dir_keeps_previous_when_invalid(qt_app: object, tmp_path: object) -> None:
    from ui_qt import MarkdownConverterQtApp

    app = MarkdownConverterQtApp()
    app.build()
    ok_dir = tmp_path / "ok"
    ok_dir.mkdir()
    app.set_output_dir(ok_dir)
    assert app.output_dir == ok_dir.resolve()
    app.set_output_dir(tmp_path / "missing")
    assert app.output_dir == ok_dir.resolve()
    assert str(ok_dir.resolve()) in (app.output_banner_parts.label.text() or "")


@pytest.mark.skipif(sys.platform == "win32", reason="chmod lecture seule non portable sous Windows")
def test_set_output_dir_rejects_non_writable(qt_app: object, tmp_path: object) -> None:
    import os

    from ui_qt import MarkdownConverterQtApp

    d = tmp_path / "readonly"
    d.mkdir()
    try:
        os.chmod(d, 0o555)
        if os.access(d, os.W_OK):
            pytest.skip("chmod n'a pas retiré l'écriture sur ce système de fichiers")
        app = MarkdownConverterQtApp()
        app.build()
        app.set_output_dir(d)
        assert app.output_dir is None
        assert app.output_banner_parts is not None
        assert "écriture" in app.output_banner_parts.error_label.text().lower()
    finally:
        os.chmod(d, 0o755)


def test_vider_clears_after_confirm(qt_app: object, tmp_path: object, monkeypatch: object) -> None:
    import PySide6.QtWidgets as qtw

    from ui_qt import MarkdownConverterQtApp, add_paths_to_model

    monkeypatch.setattr(
        qtw.QMessageBox,
        "question",
        lambda *_a, **_k: qtw.QMessageBox.StandardButton.Yes,
    )
    app = MarkdownConverterQtApp()
    app.build()
    p = tmp_path / "f.docx"
    p.write_bytes(b"x")
    add_paths_to_model(app.file_view_parts.model, [p])
    app.toolbar_parts.search_input.setText("f")
    app.toolbar_parts.chip_buttons[".docx"].setChecked(True)
    app._on_clear_file_list()
    assert len(app.file_view_parts.model.records()) == 0
    assert app.toolbar_parts.search_input.text() == ""
    assert app.file_view_parts.proxy.rowCount() == 0
    assert app.toolbar_parts.chip_buttons[".docx"].isChecked() is False


def test_vider_cancel_keeps_files(qt_app: object, tmp_path: object, monkeypatch: object) -> None:
    import PySide6.QtWidgets as qtw

    from ui_qt import MarkdownConverterQtApp, add_paths_to_model

    monkeypatch.setattr(
        qtw.QMessageBox,
        "question",
        lambda *_a, **_k: qtw.QMessageBox.StandardButton.No,
    )
    app = MarkdownConverterQtApp()
    app.build()
    p = tmp_path / "f.docx"
    p.write_bytes(b"x")
    add_paths_to_model(app.file_view_parts.model, [p])
    app._on_clear_file_list()
    assert len(app.file_view_parts.model.records()) == 1
