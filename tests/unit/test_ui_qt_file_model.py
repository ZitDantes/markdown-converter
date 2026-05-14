"""Tests du modèle de table Qt ``ConversionFileTableModel`` (PLO-35)."""

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


def test_model_vide(qt_app: object) -> None:
    from PySide6.QtCore import QModelIndex

    from ui_qt_file_model import ConversionFileTableModel

    m = ConversionFileTableModel()
    assert m.rowCount(QModelIndex()) == 0
    assert m.columnCount(QModelIndex()) == 5


def test_affichage_ligne_et_couleur_format(qt_app: object, tmp_path: Path) -> None:
    from PySide6.QtCore import QModelIndex, Qt
    from PySide6.QtGui import QColor

    from ui_qt_file_model import ConversionFileTableModel

    docx = tmp_path / "rapport.docx"
    docx.write_bytes(b"hello")
    rec = FileConversionRecord(
        source_path=docx,
        status=ConversionStatus.SUCCESS_REVIEW,
        progress_percent=0.42,
    )
    m = ConversionFileTableModel([rec])
    assert m.rowCount(QModelIndex()) == 1

    ix0 = m.index(0, 0)
    assert m.data(ix0, Qt.ItemDataRole.DisplayRole) == "DOCX"
    bg = m.data(ix0, Qt.ItemDataRole.BackgroundRole)
    assert isinstance(bg, QColor)
    assert bg.name() == "#2b6cb0"

    ix1 = m.index(0, 1)
    assert m.data(ix1, Qt.ItemDataRole.DisplayRole) == "rapport.docx"

    ix3 = m.index(0, 3)
    assert m.data(ix3, Qt.ItemDataRole.DisplayRole) == "OK · relire"

    ix4 = m.index(0, 4)
    assert m.data(ix4, Qt.ItemDataRole.DisplayRole) == "42 %"


def test_tri_par_nom(qt_app: object, tmp_path: Path) -> None:
    from PySide6.QtCore import Qt

    from ui_qt_file_model import ConversionFileTableModel

    b = tmp_path / "b.txt"
    a = tmp_path / "a.txt"
    b.write_text("b")
    a.write_text("a")
    records = [
        FileConversionRecord(source_path=b, status=ConversionStatus.SUCCESS),
        FileConversionRecord(source_path=a, status=ConversionStatus.SUCCESS),
    ]
    m = ConversionFileTableModel(records)
    m.sort(1, Qt.SortOrder.AscendingOrder)
    assert m.records()[0].source_path.name == "a.txt"
    assert m.records()[1].source_path.name == "b.txt"


def test_set_records_reset(qt_app: object, tmp_path: Path) -> None:
    from PySide6.QtCore import QModelIndex

    from ui_qt_file_model import ConversionFileTableModel

    p = tmp_path / "solo.pdf"
    p.write_bytes(b"%PDF-1.4")
    m = ConversionFileTableModel(
        [FileConversionRecord(source_path=p, status=ConversionStatus.ERROR)]
    )
    assert m.rowCount(QModelIndex()) == 1
    m.set_records([])
    assert m.rowCount(QModelIndex()) == 0


def test_conversion_status_label_fr_coherent_avec_colonne_statut() -> None:
    from ui_qt_file_model import conversion_status_label_fr

    assert conversion_status_label_fr(ConversionStatus.QUEUED) == "En attente"
    assert conversion_status_label_fr(ConversionStatus.SUCCESS_FALLBACK) == "OK · secours"


def test_format_source_file_size(qt_app: object, tmp_path: Path) -> None:
    from ui_qt_file_model import format_source_file_size

    p = tmp_path / "b.bin"
    p.write_bytes(b"x" * 2048)
    txt = format_source_file_size(p)
    assert "Ko" in txt or "o" in txt
