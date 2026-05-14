"""Tests glisser-déposer et MIME pour la file Qt (PLO-27)."""

from __future__ import annotations

import os
from pathlib import Path

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


def test_paths_from_mime_urls_filters_non_local(qt_app: object, tmp_path: Path) -> None:
    from PySide6.QtCore import QMimeData, QUrl

    from ui_qt_file_drop_table import paths_from_mime_urls

    f = tmp_path / "a.txt"
    f.write_text("x", encoding="utf-8")
    mime = QMimeData()
    mime.setUrls(
        [
            QUrl.fromLocalFile(str(f)),
            QUrl("https://example.com/doc"),
        ]
    )
    got = paths_from_mime_urls(mime)
    assert got == [f]


def test_supported_paths_from_mime_merges_files_and_dirs(qt_app: object, tmp_path: Path) -> None:
    from PySide6.QtCore import QMimeData, QUrl

    from ui_qt_file_drop_table import supported_paths_from_mime

    d = tmp_path / "src"
    d.mkdir()
    (d / "one.txt").write_text("a", encoding="utf-8")
    sub = d / "nested"
    sub.mkdir()
    (sub / "two.docx").write_bytes(b"PK\x03\x04 fake docx stub for path only")

    lone = tmp_path / "root.txt"
    lone.write_text("b", encoding="utf-8")

    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(d)), QUrl.fromLocalFile(str(lone))])
    got = supported_paths_from_mime(mime)
    assert lone.resolve() in got
    assert (d / "one.txt").resolve() in got
    assert len(got) >= 2


def test_conversion_file_drop_table_view_instantiation(qt_app: object) -> None:
    from ui_qt_file_drop_table import ConversionFileDropTableView
    from ui_qt_file_model import ConversionFileTableModel

    model = ConversionFileTableModel()
    view = ConversionFileDropTableView(model)
    view.resize(400, 200)
    assert view.acceptDrops() is True
