"""Tests du proxy de filtre Qt ``ConversionFileFilterProxy`` (PLO-36)."""

from __future__ import annotations

from pathlib import Path

import pytest

from converter import ConversionStatus, FileConversionRecord


@pytest.fixture
def qt_app() -> object:
    pytest.importorskip("PySide6", reason="PySide6 non installé localement")
    import os
    import sys

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def _records(tmp_path: Path) -> list[FileConversionRecord]:
    paths = [
        tmp_path / "rapport.docx",
        tmp_path / "annexe.docx",
        tmp_path / "presentation.pptx",
        tmp_path / "facture.pdf",
        tmp_path / "notes.txt",
    ]
    for p in paths:
        p.write_bytes(b"x")
    return [FileConversionRecord(source_path=p, status=ConversionStatus.QUEUED) for p in paths]


def test_proxy_initial_passes_everything(qt_app: object, tmp_path: Path) -> None:
    from ui_qt_file_model import ConversionFileTableModel
    from ui_qt_file_proxy import ConversionFileFilterProxy

    source = ConversionFileTableModel(_records(tmp_path))
    proxy = ConversionFileFilterProxy(source)
    assert proxy.rowCount() == 5


def test_proxy_filter_by_extension(qt_app: object, tmp_path: Path) -> None:
    from ui_qt_file_model import ConversionFileTableModel
    from ui_qt_file_proxy import ConversionFileFilterProxy

    source = ConversionFileTableModel(_records(tmp_path))
    proxy = ConversionFileFilterProxy(source)
    proxy.set_active_extensions({".docx"})
    assert proxy.rowCount() == 2

    proxy.set_active_extensions({".docx", ".pdf"})
    assert proxy.rowCount() == 3

    proxy.set_active_extensions(set())
    assert proxy.rowCount() == 5


def test_proxy_filter_by_name(qt_app: object, tmp_path: Path) -> None:
    from ui_qt_file_model import ConversionFileTableModel
    from ui_qt_file_proxy import ConversionFileFilterProxy

    source = ConversionFileTableModel(_records(tmp_path))
    proxy = ConversionFileFilterProxy(source)
    proxy.set_name_filter("RAP")
    assert proxy.rowCount() == 1
    rec = proxy.source_record_at(0)
    assert rec is not None
    assert rec.source_path.name == "rapport.docx"

    proxy.set_name_filter("")
    assert proxy.rowCount() == 5


def test_proxy_filter_cumulative(qt_app: object, tmp_path: Path) -> None:
    from ui_qt_file_model import ConversionFileTableModel
    from ui_qt_file_proxy import ConversionFileFilterProxy

    source = ConversionFileTableModel(_records(tmp_path))
    proxy = ConversionFileFilterProxy(source)
    proxy.set_active_extensions({".docx"})
    proxy.set_name_filter("annex")
    assert proxy.rowCount() == 1
    rec = proxy.source_record_at(0)
    assert rec is not None
    assert rec.source_path.name == "annexe.docx"


def test_proxy_emits_filter_changed(qt_app: object, tmp_path: Path) -> None:
    from ui_qt_file_model import ConversionFileTableModel
    from ui_qt_file_proxy import ConversionFileFilterProxy

    source = ConversionFileTableModel(_records(tmp_path))
    proxy = ConversionFileFilterProxy(source)
    received: list[int] = []
    proxy.filter_changed.connect(lambda: received.append(1))

    proxy.set_active_extensions({".pdf"})
    proxy.set_name_filter("fact")
    proxy.set_name_filter("fact")  # identique : ne doit pas re-émettre
    proxy.set_active_extensions({".pdf"})  # identique : ne doit pas re-émettre
    assert sum(received) == 2
