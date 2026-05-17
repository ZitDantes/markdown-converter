"""Tests glisser-déposer Qt → chemins (``conversion_mime_paths``, PLO-56)."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_paths_from_mime_urls_local_files(tmp_path: Path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QMimeData, QUrl

    from conversion_mime_paths import paths_from_mime_urls

    f = tmp_path / "a.txt"
    f.write_text("x", encoding="utf-8")
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(f))])
    assert paths_from_mime_urls(mime) == [f]


def test_supported_paths_from_mime_merges_dir(tmp_path: Path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QMimeData, QUrl

    from conversion_mime_paths import supported_paths_from_mime

    sub = tmp_path / "sub"
    sub.mkdir()
    doc = sub / "note.txt"
    doc.write_text("hi", encoding="utf-8")
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(sub))])
    got = supported_paths_from_mime(mime)
    assert doc.resolve() in [p.resolve() for p in got]
