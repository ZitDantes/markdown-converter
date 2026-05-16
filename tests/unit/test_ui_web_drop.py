"""Tests glisser-déposer UI web (PLO-53)."""

from __future__ import annotations

import json
import os
import sys

import pytest


@pytest.fixture
def qt_app() -> object:
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def test_web_engine_drop_view_accepts_drops(qt_app: object) -> None:
    from ui_web_drop import WebEngineDropView
    from ui_web_shell import WebBackend

    backend = WebBackend()
    view = WebEngineDropView(backend)
    view.resize(640, 480)
    assert view.acceptDrops() is True


def test_handle_drop_mime_adds_to_queue(qt_app: object, tmp_path: object) -> None:
    from PySide6.QtCore import QMimeData, QUrl

    from ui_web_shell import WebBackend

    src = tmp_path / "note.txt"
    src.write_text("hello", encoding="utf-8")
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(src))])

    backend = WebBackend()
    added_payload: list[str] = []
    backend.pathsAdded.connect(added_payload.append)
    backend.handle_drop_mime(mime)

    state = json.loads(backend.getQueueState())
    assert len(state["items"]) == 1
    assert state["items"][0]["status"] == "queued"
    assert len(added_payload) == 1
    data = json.loads(added_payload[0])
    assert data["cancelled"] is False
    assert len(data["paths"]) == 1


def test_handle_drop_mime_ignored_during_conversion(qt_app: object, tmp_path: object) -> None:
    from PySide6.QtCore import QMimeData, QUrl

    from ui_web_shell import WebBackend

    src = tmp_path / "a.txt"
    src.write_text("x", encoding="utf-8")
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(src))])

    backend = WebBackend()
    backend._worker_thread = object()  # type: ignore[assignment]
    backend.handle_drop_mime(mime)
    assert json.loads(backend.getQueueState())["items"] == []
