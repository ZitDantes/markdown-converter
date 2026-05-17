"""Signaux QWebChannel du backend web (PLO-67)."""

from __future__ import annotations

import json
import sys

import pytest


@pytest.fixture
def qt_app() -> object:
    pytest.importorskip("PySide6")
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def test_emit_queue_updated_fires_queue_updated(qt_app: object) -> None:
    from PySide6.QtTest import QSignalSpy

    from ui_web_shell import WebBackend

    backend = WebBackend()
    spy = QSignalSpy(backend.queueUpdated)
    backend._emit_queue_updated()
    assert spy.count() == 1
    payload = spy.at(0)[0]
    state = json.loads(payload)
    assert state["schemaVersion"] == "0"
    assert "items" in state


def test_worker_sink_forwards_log_to_log_emitted(qt_app: object) -> None:
    from PySide6.QtTest import QSignalSpy

    from ui_web_shell import WebBackend, _WorkerBridgeSink

    backend = WebBackend()
    sink = _WorkerBridgeSink(backend)
    spy = QSignalSpy(backend.logEmitted)
    sink.on_log("INFO", "ligne worker")
    assert spy.count() == 1
    assert spy.at(0)[0] == "INFO"
    assert spy.at(0)[1] == "ligne worker"


def test_apply_progress_emits_progress_and_queue(qt_app: object, tmp_path: object) -> None:
    from PySide6.QtTest import QSignalSpy

    from converter import ConversionStatus, FileConversionRecord
    from ui_web_shell import WebBackend

    src = tmp_path / "a.txt"
    src.write_text("x", encoding="utf-8")
    backend = WebBackend()
    backend._queue.set_records(
        [FileConversionRecord(source_path=src.resolve(), status=ConversionStatus.QUEUED)]
    )
    progress_spy = QSignalSpy(backend.progressUpdated)
    queue_spy = QSignalSpy(backend.queueUpdated)
    backend._apply_progress(0, 1, src.name, 0.5)
    assert progress_spy.count() == 1
    assert queue_spy.count() == 1
    progress = json.loads(progress_spy.at(0)[0])
    assert progress["batchPercent"] == 0.5
