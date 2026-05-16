"""Helpers inspecteur pour le pont web (PLO-51) — logique pure réutilisable."""

from __future__ import annotations

from pathlib import Path

from bridge_contract.models import InspectorPreviewResult
from converter import SUCCESS_STATUSES, FileConversionRecord
from ui_qt_inspector_data import parse_front_matter
from utils import find_existing_output_md


def read_markdown_text_for_record(record: FileConversionRecord) -> str | None:
    """Markdown produit : mémoire en priorité, sinon lecture disque."""
    if record.output_md_text is not None:
        return record.output_md_text
    out = record.output_path
    if out is None:
        return None
    try:
        return out.read_text(encoding="utf-8")
    except OSError:
        return None


def build_inspector_preview(record: FileConversionRecord) -> InspectorPreviewResult:
    """Construit le DTO d'aperçu pour un enregistrement de file."""
    if record.status not in SUCCESS_STATUSES:
        msg = (record.message or "").strip() or "Aucun Markdown disponible pour ce fichier."
        return InspectorPreviewResult(ok=False, message=msg)

    text = read_markdown_text_for_record(record)
    if text is None:
        return InspectorPreviewResult(
            ok=False,
            message="Le fichier Markdown produit est introuvable ou illisible.",
        )

    parsed = parse_front_matter(text)
    warning = parsed.front_matter.get("avertissement", "").strip() or None
    return InspectorPreviewResult(
        ok=True,
        frontMatter=dict(parsed.front_matter),
        body=parsed.body,
        warning=warning,
    )


def _path_key(path: Path) -> str:
    try:
        return str(path.resolve())
    except OSError:
        return str(path)


def record_for_source_path(
    records: list[FileConversionRecord],
    source_path: str,
) -> FileConversionRecord | None:
    target_key = _path_key(Path(source_path))
    for rec in records:
        if _path_key(rec.source_path) == target_key:
            return rec
    return None


def resolve_output_path(
    record: FileConversionRecord,
    output_dir: Path | None,
) -> Path | None:
    """Chemin du .md produit (record ou déduction depuis le dossier de sortie)."""
    if record.output_path is not None:
        try:
            if record.output_path.exists():
                return record.output_path.resolve()
        except OSError:
            return record.output_path
    if output_dir is None:
        return None
    found = find_existing_output_md(output_dir, record.source_path.stem)
    if found is not None:
        return found.resolve()
    return record.output_path
