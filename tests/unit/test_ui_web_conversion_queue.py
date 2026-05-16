"""File de conversion web : statuts après conversion (PLO-52)."""

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


def test_merge_summary_by_index_preserves_queue_paths(qt_app: object, tmp_path: object) -> None:
    """Fusion par index : les chemins de la file UI restent les clés inspecteur."""
    from converter import ConversionStatus, ConversionSummary, FileConversionRecord
    from ui_web_shell import WebBackend

    queue_path = tmp_path / "doc.docx"
    queue_path.write_bytes(b"fake")
    summary_path = (tmp_path / "other").resolve() / "doc.docx"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_bytes(b"fake")

    backend = WebBackend()
    backend._queue.set_records(
        [FileConversionRecord(source_path=queue_path.resolve(), status=ConversionStatus.QUEUED)]
    )
    summary = ConversionSummary(
        started_at=__import__("datetime").datetime.now(),
        finished_at=__import__("datetime").datetime.now(),
        output_dir=tmp_path,
        records=[
            FileConversionRecord(
                source_path=summary_path,
                status=ConversionStatus.SUCCESS,
                progress_percent=1.0,
            )
        ],
    )
    backend._merge_summary_records(summary)
    rec = backend._queue.records()[0]
    assert rec.source_path == queue_path.resolve()
    assert rec.status == ConversionStatus.SUCCESS


def test_web_conversion_updates_queue_status(qt_app: object, tmp_path: object) -> None:
    from PySide6.QtCore import QTimer

    from converter import ConversionStatus, FileConversionRecord
    from ui_web_shell import WebBackend

    src = tmp_path / "note.txt"
    src.write_text("contenu de test pour conversion", encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()

    backend = WebBackend()
    backend._output_dir = out.resolve()
    backend._queue.set_records(
        [FileConversionRecord(source_path=src.resolve(), status=ConversionStatus.QUEUED)]
    )

    cmd = json.dumps({"schemaVersion": "0", "useConversionFallback": True})
    raw_ack = backend.startConversion(cmd)
    ack = json.loads(raw_ack)
    assert ack["ok"] is True

    def _finish() -> None:
        if backend._worker_thread is not None:
            QTimer.singleShot(50, _finish)
            return
        state = json.loads(backend.getQueueState())
        assert len(state["items"]) == 1
        assert state["items"][0]["status"] == "success"
        assert state["items"][0]["statusLabel"] == "OK"
        qt_app.quit()

    QTimer.singleShot(50, _finish)
    qt_app.exec()
