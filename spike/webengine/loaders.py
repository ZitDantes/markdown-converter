"""Résolution des URL de page pour le spike (``file:`` vs ``qrc:``)."""

from __future__ import annotations

import enum
import os
from pathlib import Path

from PySide6.QtCore import QUrl

_SPIKE_DIR = Path(__file__).resolve().parent
_STATIC_FILE_DIR = _SPIKE_DIR / "static_file"


class LoaderMode(enum.StrEnum):
    FILE = "file"
    QRC = "qrc"


def resolve_page_url(mode: LoaderMode) -> QUrl:
    """Retourne l'URL de la page HTML selon le mode demandé."""
    if mode == LoaderMode.FILE:
        index = _STATIC_FILE_DIR / "index.html"
        if not index.is_file():
            msg = f"Page spike introuvable : {index}"
            raise FileNotFoundError(msg)
        return QUrl.fromLocalFile(os.fspath(index.resolve()))
    if mode == LoaderMode.QRC:
        # Alias dans resources.qrc ; forme « qrc:/// » attendue par WebEngine.
        import spike.webengine.resources_rc  # noqa: F401 — enregistre les ressources

        return QUrl("qrc:///spike/index.html")
    msg = f"Mode de chargement inconnu : {mode!r}"
    raise ValueError(msg)
