"""Tests du module ``ui_conversion_display`` (sans PySide6)."""

from __future__ import annotations

from pathlib import Path

from converter import ConversionStatus
from ui_conversion_display import (
    conversion_status_label_fr,
    file_byte_size,
    format_byte_size,
    format_source_file_size,
)


def test_format_byte_size() -> None:
    assert format_byte_size(0) == "0 o"
    assert "Ko" in format_byte_size(2048) or "o" in format_byte_size(2048)


def test_file_byte_size(tmp_path: Path) -> None:
    p = tmp_path / "x.txt"
    p.write_text("abc")
    assert file_byte_size(p) == 3


def test_conversion_status_label_fr() -> None:
    assert conversion_status_label_fr(ConversionStatus.QUEUED) == "En attente"
    assert conversion_status_label_fr(ConversionStatus.SUCCESS) == "OK"


def test_format_source_file_size(tmp_path: Path) -> None:
    p = tmp_path / "b.bin"
    p.write_bytes(b"x" * 100)
    assert format_source_file_size(p) == format_byte_size(file_byte_size(p))
