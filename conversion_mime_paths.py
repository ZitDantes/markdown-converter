"""Chemins issus d'un glisser-déposer Qt (``QMimeData``)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from utils import merge_file_lists

if TYPE_CHECKING:
    from PySide6.QtCore import QMimeData


def paths_from_mime_urls(mime: QMimeData) -> list[Path]:
    """Extrait les chemins locaux à partir d'un ``QMimeData`` (URLs ``file://``)."""
    if not mime.hasUrls():
        return []
    out: list[Path] = []
    for url in mime.urls():
        if not url.isLocalFile():
            continue
        raw = url.toLocalFile()
        if not raw:
            continue
        out.append(Path(raw))
    return out


def supported_paths_from_mime(mime: QMimeData) -> list[Path]:
    """Chemins de fichiers supportés issus d'un glisser-déposer (fichiers + dossiers)."""
    paths = paths_from_mime_urls(mime)
    files = [p for p in paths if p.exists() and p.is_file()]
    dirs = [p for p in paths if p.exists() and p.is_dir()]
    supported, _unsupported = merge_file_lists(files, dirs)
    return supported
