"""Tests journal / fichier de log backend web (PLO-52)."""

from __future__ import annotations

import json

import pytest


@pytest.fixture
def qt_app() -> object:
    pytest.importorskip("PySide6")
    import os
    import sys

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def test_get_log_file_path(qt_app: object) -> None:
    from ui_web_shell import WebBackend

    backend = WebBackend()
    raw = json.loads(backend.getLogFilePath())
    assert raw["schemaVersion"] == "0"
    assert raw["path"]
    assert raw["path"].endswith(".log") or "run.log" in raw["path"]
