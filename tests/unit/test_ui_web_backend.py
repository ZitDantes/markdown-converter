"""Tests du backend WebChannel (PLO-46)."""

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


def test_web_backend_ping_and_queue(qt_app: object) -> None:
    from ui_web_shell import WebBackend

    backend = WebBackend()
    assert backend.ping("test") == "pong:test"
    data = json.loads(backend.getQueueState())
    assert data["schemaVersion"] == "0"
    assert data["items"] == []
    assert data["canStartConversion"] is False


def test_start_worker_keeps_sink_reference(qt_app: object, tmp_path: object) -> None:
    """``_start_worker`` doit conserver ``_worker_sink`` (référence forte pour les signaux)."""
    from converter import ConversionStatus, FileConversionRecord
    from ui_web_shell import WebBackend, _WorkerBridgeSink

    src = tmp_path / "note.txt"
    src.write_text("hello", encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()

    backend = WebBackend()
    backend._queue.set_records(
        [FileConversionRecord(source_path=src, status=ConversionStatus.QUEUED)]
    )

    backend._start_worker([src], out, use_conversion_fallback=True)
    assert isinstance(backend._worker_sink, _WorkerBridgeSink)

    thread = backend._worker_thread
    assert thread is not None
    thread.quit()
    assert thread.wait(10_000)
