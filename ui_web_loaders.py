"""Chargement de l'UI web buildée (``web/dist/``) pour ``ui_web_shell`` (PLO-46)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtCore import QUrl


def bundle_resource_root() -> Path:
    """Racine des ressources embarquées (dépôt ou bundle PyInstaller)."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
    return Path(__file__).resolve().parent


def web_dist_index_path() -> Path:
    """Chemin vers ``web/dist/index.html``."""
    return bundle_resource_root() / "web" / "dist" / "index.html"


def resolve_web_index_url() -> QUrl:
    """URL ``file:`` vers l'index Vite (dev ou release embarquée)."""
    from PySide6.QtCore import QUrl

    index = web_dist_index_path()
    if not index.is_file():
        msg = (
            f"Interface web introuvable : {index}\n\n"
            "Construisez le front une fois :\n"
            "  cd web && npm ci && npm run build\n"
            "  ou : ./scripts/build_web.sh"
        )
        raise FileNotFoundError(msg)
    return QUrl.fromLocalFile(os.fspath(index.resolve()))
