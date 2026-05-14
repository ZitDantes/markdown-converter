"""Tests du renommage en lot des sorties Markdown (PLO-38)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from converter import ConversionStatus, FileConversionRecord
from ui_qt_inspector_rename import (
    CASE_LOWER,
    CASE_TITLE,
    CASE_UNCHANGED,
    CASE_UPPER,
    RenameOp,
    build_new_output_path,
    execute_rename_plan,
    plan_bulk_rename,
    transform_stem,
    validate_affixes,
)


def test_transform_stem() -> None:
    assert transform_stem("AbC", CASE_LOWER) == "abc"
    assert transform_stem("AbC", CASE_UPPER) == "ABC"
    assert transform_stem("hello world", CASE_TITLE) == "Hello World"
    assert transform_stem("x", CASE_UNCHANGED) == "x"


def test_validate_affixes_rejects_slash() -> None:
    err = validate_affixes("pre/fix", "")
    assert err is not None


def test_build_new_output_path() -> None:
    old = Path("/tmp/out/doc.md")
    assert build_new_output_path(old, "p_", "_s", CASE_LOWER) == Path("/tmp/out/p_doc_s.md")


def test_plan_prefix_two_files(tmp_path: Path) -> None:
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("1")
    b.write_text("2")
    r1 = FileConversionRecord(
        source_path=tmp_path / "s1.docx", status=ConversionStatus.SUCCESS, output_path=a
    )
    r2 = FileConversionRecord(
        source_path=tmp_path / "s2.docx", status=ConversionStatus.SUCCESS, output_path=b
    )
    ops, err = plan_bulk_rename([r1, r2], "PRE_", "", CASE_UNCHANGED)
    assert err is None
    assert len(ops) == 2
    assert ops[0].new_path.name == "PRE_a.md"


def test_plan_rejects_existing_target_not_in_batch(tmp_path: Path) -> None:
    out = tmp_path / "a.md"
    out.write_text("x")
    blocker = tmp_path / "PRE_a.md"
    blocker.write_text("block")
    r = FileConversionRecord(
        source_path=tmp_path / "s.docx", status=ConversionStatus.SUCCESS, output_path=out
    )
    ops, err = plan_bulk_rename([r], "PRE_", "", CASE_UNCHANGED)
    assert ops == []
    assert err is not None
    assert "existe déjà" in err


def test_plan_skips_non_success(tmp_path: Path) -> None:
    p = tmp_path / "x.md"
    p.write_text("1")
    r = FileConversionRecord(
        source_path=tmp_path / "s.docx", status=ConversionStatus.ERROR, output_path=p
    )
    ops, err = plan_bulk_rename([r], "p", "", CASE_UNCHANGED)
    assert err is None
    assert ops == []


def test_execute_prefix_updates_disk_and_records(tmp_path: Path) -> None:
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("A")
    b.write_text("B")
    r1 = FileConversionRecord(
        source_path=tmp_path / "s1.docx", status=ConversionStatus.SUCCESS, output_path=a
    )
    r2 = FileConversionRecord(
        source_path=tmp_path / "s2.docx", status=ConversionStatus.SUCCESS, output_path=b
    )
    ops, err = plan_bulk_rename([r1, r2], "N_", "", CASE_UNCHANGED)
    assert err is None
    assert execute_rename_plan(ops) == (True, "")
    assert r1.output_path == tmp_path / "N_a.md"
    assert r2.output_path == tmp_path / "N_b.md"
    assert r1.output_path.read_text() == "A"
    assert not a.exists()


@pytest.mark.skipif(
    sys.platform == "darwin" or sys.platform == "win32",
    reason="Nécessite un FS sensible à la casse pour deux noms qui ne diffèrent que par la casse",
)
def test_plan_rejects_duplicate_targets_after_case_lower(tmp_path: Path) -> None:
    d = tmp_path / "d"
    d.mkdir()
    p1 = d / "Foo.md"
    p2 = d / "foo.md"
    p1.write_text("1")
    p2.write_text("2")
    r1 = FileConversionRecord(
        source_path=tmp_path / "s1.docx", status=ConversionStatus.SUCCESS, output_path=p1
    )
    r2 = FileConversionRecord(
        source_path=tmp_path / "s2.docx", status=ConversionStatus.SUCCESS, output_path=p2
    )
    ops, err = plan_bulk_rename([r1, r2], "", "", CASE_LOWER)
    assert ops == []
    assert err is not None
    assert "même nom" in err


def test_execute_swap_two_files(tmp_path: Path) -> None:
    p1 = tmp_path / "a.md"
    p2 = tmp_path / "b.md"
    p1.write_text("A")
    p2.write_text("B")
    r1 = FileConversionRecord(
        source_path=tmp_path / "s1.docx", status=ConversionStatus.SUCCESS, output_path=p1
    )
    r2 = FileConversionRecord(
        source_path=tmp_path / "s2.docx", status=ConversionStatus.SUCCESS, output_path=p2
    )
    ops = [RenameOp(r1, p1, p2), RenameOp(r2, p2, p1)]
    assert execute_rename_plan(ops) == (True, "")
    assert r1.output_path == p2
    assert r2.output_path == p1
    assert p1.read_text() == "B"
    assert p2.read_text() == "A"
