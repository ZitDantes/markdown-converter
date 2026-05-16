"""
DTOs et sérialisation JSON du pont WebChannel (contrat v0, PLO-45).

Voir ``docs/adr/0001-contrat-pont-webchannel-js-python.md``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, TypeVar

from converter import ConversionSummary, FileConversionRecord
from ui_conversion_display import (
    conversion_status_label_fr,
    file_byte_size,
    format_accent_hex,
    format_byte_size,
    format_monogram_for_path,
)
from utils import normalize_extension

SCHEMA_VERSION = "0"
BACKEND_OBJECT_NAME = "backend"

T = TypeVar("T")


def dumps_json(payload: dict[str, Any]) -> str:
    """Sérialise un message racine avec ``schemaVersion`` implicite si absent."""
    data = dict(payload)
    data.setdefault("schemaVersion", SCHEMA_VERSION)
    return json.dumps(data, ensure_ascii=False)


def loads_json(text: str) -> dict[str, Any]:
    data = json.loads(text)
    if not isinstance(data, dict):
        msg = "Payload JSON attendu : objet"
        raise TypeError(msg)
    return data


@dataclass
class FileQueueItem:
    sourcePath: str
    status: str
    statusLabel: str
    progressPercent: float
    fileName: str
    parentDir: str
    extension: str
    sizeLabel: str
    sizeBytes: int
    formatColor: str
    formatMonogram: str
    outputPath: str | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QueueState:
    items: list[FileQueueItem] = field(default_factory=list)
    outputDir: str | None = None
    canStartConversion: bool = False
    totalSizeLabel: str = "0 o"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "items": [i.to_dict() for i in self.items],
            "outputDir": self.outputDir,
            "canStartConversion": self.canStartConversion,
            "totalSizeLabel": self.totalSizeLabel,
        }


@dataclass
class ProgressEvent:
    fileIndex: int
    fileTotal: int
    fileLabel: str
    batchPercent: float

    def to_dict(self) -> dict[str, Any]:
        return {"schemaVersion": SCHEMA_VERSION, **asdict(self)}


@dataclass
class ConversionSummaryDto:
    startedAt: str
    finishedAt: str
    outputDir: str
    records: list[FileQueueItem]
    unsupportedSkipped: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "startedAt": self.startedAt,
            "finishedAt": self.finishedAt,
            "outputDir": self.outputDir,
            "records": [r.to_dict() for r in self.records],
            "unsupportedSkipped": self.unsupportedSkipped,
            "warnings": self.warnings,
        }


@dataclass
class ConversionFinishedEvent:
    summary: ConversionSummaryDto

    def to_dict(self) -> dict[str, Any]:
        return {"schemaVersion": SCHEMA_VERSION, "summary": self.summary.to_dict()}


@dataclass
class StartConversionCommand:
    useConversionFallback: bool = True

    @classmethod
    def from_json(cls, text: str) -> StartConversionCommand:
        data = loads_json(text)
        return cls(useConversionFallback=bool(data.get("useConversionFallback", True)))


@dataclass
class AckResult:
    ok: bool
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "ok": self.ok,
            "message": self.message,
        }


@dataclass
class PickFilesResult:
    paths: list[str] = field(default_factory=list)
    cancelled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "paths": self.paths,
            "cancelled": self.cancelled,
        }


@dataclass
class PickFolderResult:
    path: str | None = None
    cancelled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "path": self.path,
            "cancelled": self.cancelled,
        }


@dataclass
class SetOutputDirResult:
    ok: bool
    outputDir: str | None = None
    errorMessage: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "ok": self.ok,
            "outputDir": self.outputDir,
            "errorMessage": self.errorMessage,
        }


@dataclass
class ClearQueueResult:
    clearedCount: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "clearedCount": self.clearedCount,
        }


def file_queue_item_from_record(record: FileConversionRecord) -> FileQueueItem:
    """Construit un DTO file pour le front (libellé PLO-33 via ``conversion_status_label_fr``)."""
    path = record.source_path
    size_bytes = file_byte_size(path)
    ext = normalize_extension(path)
    return FileQueueItem(
        sourcePath=str(path),
        status=record.status.value,
        statusLabel=conversion_status_label_fr(record.status),
        progressPercent=record.progress_percent,
        fileName=path.name,
        parentDir=str(path.parent),
        extension=ext,
        sizeLabel=format_byte_size(size_bytes),
        sizeBytes=size_bytes,
        formatColor=format_accent_hex(ext),
        formatMonogram=format_monogram_for_path(path),
        outputPath=str(record.output_path) if record.output_path else None,
        message=record.message,
    )


def summary_dto_from_summary(summary: ConversionSummary) -> ConversionSummaryDto:
    return ConversionSummaryDto(
        startedAt=summary.started_at.isoformat(),
        finishedAt=summary.finished_at.isoformat(),
        outputDir=str(summary.output_dir),
        records=[file_queue_item_from_record(r) for r in summary.records],
        unsupportedSkipped=[str(p) for p in summary.unsupported_skipped],
        warnings=list(summary.warnings),
    )


def progress_event_from_worker(
    index: int,
    total: int,
    label: str,
    batch_percent: float,
) -> ProgressEvent:
    return ProgressEvent(
        fileIndex=index,
        fileTotal=total,
        fileLabel=label,
        batchPercent=batch_percent,
    )
