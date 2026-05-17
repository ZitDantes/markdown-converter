"""Tests de la file partagée ``conversion_queue`` (PLO-56)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conversion_queue import add_paths_to_model


@pytest.fixture
def qt_app() -> object:
    pytest.importorskip("PySide6", reason="PySide6 non installé localement")
    import os
    import sys

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def test_add_paths_to_model_filters_and_dedupes(qt_app: object, tmp_path: Path) -> None:
    from ui_qt_file_model import ConversionFileTableModel

    supported = tmp_path / "doc.txt"
    supported.write_text("x", encoding="utf-8")
    unsupported = tmp_path / "bad.xyz"
    unsupported.write_text("y", encoding="utf-8")

    model = ConversionFileTableModel()
    added = add_paths_to_model(model, [supported, unsupported, supported])
    assert added == [supported]
    assert len(model.records()) == 1
    again = add_paths_to_model(model, [supported])
    assert again == []
