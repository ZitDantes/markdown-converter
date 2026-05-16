"""Tests slots inspecteur du backend web (PLO-51)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def qt_app() -> object:
    pytest.importorskip("PySide6")
    import os
    import sys

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def test_get_inspector_preview_success(qt_app: object, tmp_path: Path) -> None:
    from converter import ConversionStatus, FileConversionRecord
    from ui_web_shell import WebBackend

    md = "---\n---\n\nCorps\n"
    out = tmp_path / "out.md"
    out.write_text(md, encoding="utf-8")
    src = tmp_path / "a.txt"
    src.write_text("x", encoding="utf-8")

    backend = WebBackend()
    backend._queue.set_records(
        [
            FileConversionRecord(
                source_path=src,
                status=ConversionStatus.SUCCESS,
                output_path=out,
                output_md_text=md,
            )
        ]
    )

    raw = json.loads(backend.getInspectorPreview(str(src)))
    assert raw["ok"] is True
    assert "Corps" in (raw.get("body") or "")


def test_get_inspector_output_path(qt_app: object, tmp_path: Path) -> None:
    from converter import ConversionStatus, FileConversionRecord
    from ui_web_shell import WebBackend

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    md = out_dir / "a.md"
    md.write_text("ok", encoding="utf-8")
    src = tmp_path / "a.txt"
    src.write_text("x", encoding="utf-8")

    backend = WebBackend()
    backend._output_dir = out_dir
    backend._queue.set_records(
        [FileConversionRecord(source_path=src, status=ConversionStatus.SUCCESS)]
    )

    raw = json.loads(backend.getInspectorOutputPath(str(src)))
    assert raw["ok"] is True
    assert raw["outputPath"].endswith("a.md")


def test_plan_bulk_rename_preview(qt_app: object, tmp_path: Path) -> None:
    from converter import ConversionStatus, FileConversionRecord
    from ui_web_shell import WebBackend

    out1 = tmp_path / "alpha.md"
    out2 = tmp_path / "beta.md"
    out1.write_text("a", encoding="utf-8")
    out2.write_text("b", encoding="utf-8")
    r1 = FileConversionRecord(
        source_path=tmp_path / "1.txt",
        status=ConversionStatus.SUCCESS,
        output_path=out1,
    )
    r2 = FileConversionRecord(
        source_path=tmp_path / "2.txt",
        status=ConversionStatus.SUCCESS,
        output_path=out2,
    )

    backend = WebBackend()
    backend._queue.set_records([r1, r2])

    raw = json.loads(
        backend.planBulkRename(
            json.dumps(
                {"schemaVersion": "0", "prefix": "pre-", "suffix": "", "caseMode": "unchanged"}
            )
        )
    )
    assert raw["ok"] is True
    assert raw["operationCount"] == 2
    assert len(raw["previewLines"]) == 2
