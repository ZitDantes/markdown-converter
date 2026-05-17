"""File d'attente de conversion partagée (UI web)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from converter import ConversionStatus, FileConversionRecord
from utils import is_supported_path

if TYPE_CHECKING:
    from ui_qt_file_model import ConversionFileTableModel


def add_paths_to_model(model: ConversionFileTableModel, paths: list[Path]) -> list[Path]:
    """Ajoute les chemins inconnus à ``model`` en statut ``QUEUED``.

    Retourne la liste des chemins effectivement ajoutés.
    """
    existing = {rec.source_path.resolve() for rec in model.records()}
    added: list[Path] = []
    for p in paths:
        rp = p.resolve()
        if rp in existing or not is_supported_path(rp):
            continue
        model.append_record(
            FileConversionRecord(
                source_path=rp,
                status=ConversionStatus.QUEUED,
            )
        )
        existing.add(rp)
        added.append(rp)
    return added
