"""
Tests de progression du lot : ``_batch_percent_0_1``, adaptateur ``on_progress``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from converter import (
    ConversionStatus,
    FileConversionRecord,
    _batch_percent_0_1,
    _wrap_progress_callback,
)


@pytest.mark.parametrize(
    ("idx", "total", "file_part", "expected"),
    [
        (1, 10, 0.0, 0.0),
        (1, 10, 1.0, 0.1),
        (10, 10, 1.0, 1.0),
        (2, 4, 0.5, 0.375),
        (1, 1, 0.0, 0.0),
        (1, 1, 1.0, 1.0),
    ],
)
def test_batch_percent(idx: int, total: int, file_part: float, expected: float) -> None:
    assert _batch_percent_0_1(idx, total, file_part) == pytest.approx(expected)


def test_batch_percent_total_zero() -> None:
    assert _batch_percent_0_1(1, 0, 0.5) == 1.0


def test_wrap_progress_three_arg_ignores_percent() -> None:
    calls: list[tuple[int, int, str]] = []

    def legacy(i: int, t: int, lab: str) -> None:
        calls.append((i, t, lab))

    wrapped = _wrap_progress_callback(legacy)
    wrapped(0, 3, "f.txt", 0.12)
    wrapped(1, 3, "f.txt", 0.45)
    assert calls == [(0, 3, "f.txt"), (1, 3, "f.txt")]


def test_wrap_progress_four_arg_receives_percent() -> None:
    calls: list[tuple[int, int, str, float]] = []

    def extended(i: int, t: int, lab: str, pct: float) -> None:
        calls.append((i, t, lab, pct))

    wrapped = _wrap_progress_callback(extended)
    wrapped(0, 2, "a", 0.0)
    wrapped(1, 2, "a", 0.5)
    assert calls == [(0, 2, "a", 0.0), (1, 2, "a", 0.5)]


def test_wrap_progress_none_is_noop() -> None:
    wrapped = _wrap_progress_callback(None)
    wrapped(0, 1, "x", 1.0)


def test_file_record_default_progress() -> None:
    r = FileConversionRecord(
        source_path=Path("x.txt"),
        status=ConversionStatus.SUCCESS,
    )
    assert r.progress_percent == 0.0
