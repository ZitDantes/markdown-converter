"""Tests du contrat pont v0 (PLO-45)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from bridge_contract import (
    SCHEMA_VERSION,
    ConversionFinishedEvent,
    QueueState,
    StartConversionCommand,
    file_queue_item_from_record,
    summary_dto_from_summary,
)
from bridge_contract.models import progress_event_from_worker
from converter import ConversionStatus, ConversionSummary, FileConversionRecord


def test_file_queue_item_uses_french_status_label() -> None:
    rec = FileConversionRecord(
        source_path=Path("/tmp/doc.pdf"),
        status=ConversionStatus.SUCCESS_REVIEW,
        progress_percent=1.0,
    )
    item = file_queue_item_from_record(rec)
    assert item.status == "success_review"
    assert item.statusLabel == "OK · relire"
    assert item.fileName == "doc.pdf"
    assert item.formatMonogram == "PDF"
    assert item.sizeBytes >= 0
    assert "Pandoc" not in item.statusLabel
    assert "MarkItDown" not in item.statusLabel


def test_queue_state_roundtrip_json() -> None:
    state = QueueState(
        items=[
            file_queue_item_from_record(
                FileConversionRecord(
                    source_path=Path("/tmp/a.docx"),
                    status=ConversionStatus.QUEUED,
                    progress_percent=0.0,
                )
            )
        ],
        outputDir="/out",
        canStartConversion=True,
        totalSizeLabel="1,2 Ko",
    )
    raw = json.dumps(state.to_dict(), ensure_ascii=False)
    data = json.loads(raw)
    assert data["schemaVersion"] == SCHEMA_VERSION
    assert data["canStartConversion"] is True
    assert data["items"][0]["statusLabel"] == "En attente"


def test_start_conversion_command_from_json() -> None:
    cmd = StartConversionCommand.from_json('{"schemaVersion":"0","useConversionFallback":false}')
    assert cmd.useConversionFallback is False


def test_summary_dto_from_conversion_summary() -> None:
    started = datetime(2026, 5, 16, 10, 0, 0)
    finished = datetime(2026, 5, 16, 10, 1, 0)
    summary = ConversionSummary(
        started_at=started,
        finished_at=finished,
        output_dir=Path("/out"),
        records=[
            FileConversionRecord(
                source_path=Path("f.txt"),
                status=ConversionStatus.SUCCESS,
                progress_percent=1.0,
            )
        ],
        warnings=["avertissement test"],
    )
    dto = summary_dto_from_summary(summary)
    event = ConversionFinishedEvent(summary=dto)
    payload = json.loads(json.dumps(event.to_dict()))
    assert payload["schemaVersion"] == SCHEMA_VERSION
    assert payload["summary"]["records"][0]["statusLabel"] == "OK"
    assert payload["summary"]["warnings"] == ["avertissement test"]


def test_progress_event_schema() -> None:
    ev = progress_event_from_worker(2, 5, "rapport.docx", 0.4)
    data = json.loads(json.dumps(ev.to_dict()))
    assert data["fileIndex"] == 2
    assert data["batchPercent"] == 0.4
