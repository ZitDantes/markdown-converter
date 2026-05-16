"""Tests helpers inspecteur pont web (PLO-51)."""

from __future__ import annotations

from pathlib import Path

from bridge_contract.inspector_helpers import (
    build_inspector_preview,
    read_markdown_text_for_record,
    resolve_output_path,
)
from converter import ConversionStatus, FileConversionRecord


def test_read_markdown_prefers_memory(tmp_path: Path) -> None:
    out = tmp_path / "out.md"
    out.write_text("disque", encoding="utf-8")
    rec = FileConversionRecord(
        source_path=tmp_path / "a.txt",
        status=ConversionStatus.SUCCESS,
        output_path=out,
        output_md_text="mémoire",
    )
    assert read_markdown_text_for_record(rec) == "mémoire"


def test_build_inspector_preview_parses_front_matter(tmp_path: Path) -> None:
    md = '---\navertissement: "Relire le PDF"\n---\n\n# Titre\n'
    rec = FileConversionRecord(
        source_path=tmp_path / "doc.pdf",
        status=ConversionStatus.SUCCESS_REVIEW,
        output_md_text=md,
    )
    preview = build_inspector_preview(rec)
    assert preview.ok is True
    assert preview.warning == "Relire le PDF"
    assert preview.body is not None
    assert "# Titre" in preview.body


def test_resolve_output_path_from_disk(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    md = out_dir / "note.md"
    md.write_text("# x", encoding="utf-8")
    src = tmp_path / "note.txt"
    src.write_text("a", encoding="utf-8")
    rec = FileConversionRecord(source_path=src, status=ConversionStatus.SUCCESS)
    resolved = resolve_output_path(rec, out_dir)
    assert resolved is not None
    assert resolved.name == "note.md"


def test_build_inspector_preview_non_success_message() -> None:
    rec = FileConversionRecord(
        source_path=Path("/tmp/x.pdf"),
        status=ConversionStatus.ERROR,
        message="Échec moteur",
    )
    preview = build_inspector_preview(rec)
    assert preview.ok is False
    assert preview.message == "Échec moteur"
