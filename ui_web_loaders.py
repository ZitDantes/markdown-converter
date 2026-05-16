"""Chargement de l'UI web buildée (``web/dist/``) pour ``ui_web_shell`` (PLO-46)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtCore import QUrl

_REPO_ROOT = Path(__file__).resolve().parent
_WEB_DIST_INDEX = _REPO_ROOT / "web" / "dist" / "index.html"


def web_dist_index_path() -> Path:
    """Chemin vers ``web/dist/index.html``."""
    return _WEB_DIST_INDEX


def resolve_web_index_url() -> QUrl:
    """URL ``file:`` vers l'index Vite (mode dev / release non embarquée)."""
    from PySide6.QtCore import QUrl

    index = _WEB_DIST_INDEX
    if not index.is_file():
        msg = (
            f"Interface web introuvable : {index}\n\n"
            "Construisez le front une fois :\n"
            "  cd web && npm ci && npm run build\n"
            "ou : ./scripts/build_web.sh"
        )
        raise FileNotFoundError(msg)
    return QUrl.fromLocalFile(os.fspath(index.resolve()))
