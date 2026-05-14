"""
Renommage en lot des fichiers Markdown produits (PLO-38, onglet Sortie).

Logique pure (sans Qt) : planification avec validation « tout ou rien »,
puis exécution en deux phases (fichier temporaire intermédiaire) pour gérer
les permutations de noms sans écrasement accidentel.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from converter import ConversionStatus, FileConversionRecord

_RENAMEABLE_STATUSES: frozenset[ConversionStatus] = frozenset(
    {
        ConversionStatus.SUCCESS,
        ConversionStatus.SUCCESS_REVIEW,
        ConversionStatus.SUCCESS_FALLBACK,
    }
)

# Caractères interdits dans le préfixe / suffixe (chemins réservés).
_FORBIDDEN_IN_AFFIX = frozenset('<>:"/\\|?*\n\r\t')

CASE_UNCHANGED = "unchanged"
CASE_LOWER = "lower"
CASE_UPPER = "upper"
CASE_TITLE = "title"


@dataclass(frozen=True)
class RenameOp:
    """Une opération de renommage ``old_path`` → ``new_path``."""

    record: FileConversionRecord
    old_path: Path
    new_path: Path


def transform_stem(stem: str, case_mode: str) -> str:
    """Applique la casse demandée au stem (sans extension ``.md``)."""
    if case_mode == CASE_LOWER:
        return stem.lower()
    if case_mode == CASE_UPPER:
        return stem.upper()
    if case_mode == CASE_TITLE:
        return stem.title()
    return stem


def validate_affixes(prefix: str, suffix: str) -> str | None:
    """Retourne un message d'erreur en français ou ``None`` si OK."""
    for ch in prefix + suffix:
        if ch in _FORBIDDEN_IN_AFFIX:
            return (
                "Le préfixe et le suffixe ne peuvent pas contenre de barres obliques, "
                "de deux-points ni d'autres caractères réservés pour un nom de fichier."
            )
    return None


def build_new_output_path(old_path: Path, prefix: str, suffix: str, case_mode: str) -> Path:
    """Construit le chemin cible dans le même dossier que ``old_path``."""
    stem = old_path.stem
    core = f"{prefix}{transform_stem(stem, case_mode)}{suffix}"
    return old_path.parent / f"{core}.md"


def _paths_equivalent(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except OSError:
        return a == b


def _norm_key(p: Path) -> str:
    try:
        return str(p.resolve())
    except OSError:
        return str(p)


def plan_bulk_rename(
    records: Sequence[FileConversionRecord],
    prefix: str,
    suffix: str,
    case_mode: str,
) -> tuple[list[RenameOp], str | None]:
    """Construit la liste des renommages ou retourne ``( [], message_erreur )``."""
    err = validate_affixes(prefix, suffix)
    if err:
        return [], err

    ops: list[RenameOp] = []
    for rec in records:
        if rec.status not in _RENAMEABLE_STATUSES or rec.output_path is None:
            continue
        old = rec.output_path
        if old.suffix.lower() != ".md":
            continue
        new = build_new_output_path(old, prefix, suffix, case_mode)
        if _paths_equivalent(old, new):
            continue
        core = f"{prefix}{transform_stem(old.stem, case_mode)}{suffix}"
        if not core.strip():
            return [], "Le nom résultant serait vide : ajustez le préfixe, le suffixe ou la casse."
        ops.append(RenameOp(record=rec, old_path=old, new_path=new))

    if not ops:
        return [], None

    new_keys = [_norm_key(op.new_path) for op in ops]
    if len(set(new_keys)) < len(new_keys):
        return [], (
            "Conflit : plusieurs fichiers produiraient le même nom cible. "
            "Modifiez le préfixe, le suffixe ou la casse."
        )

    old_keys = {_norm_key(op.old_path) for op in ops}
    for op in ops:
        new_p = op.new_path
        if not new_p.exists():
            continue
        nk = _norm_key(new_p)
        ok_old = _norm_key(op.old_path)
        if nk == ok_old:
            continue
        if nk in old_keys:
            continue
        return [], f"Le fichier cible existe déjà sur le disque : {new_p}"

    return ops, None


def execute_rename_plan(ops: Iterable[RenameOp]) -> tuple[bool, str]:
    """Applique le plan (deux phases + rollback). Retourne ``(True, \"\")`` ou ``(False, msg)``."""
    work = [op for op in ops if not _paths_equivalent(op.old_path, op.new_path)]
    if not work:
        return True, ""

    staged: list[tuple[Path, Path, Path, FileConversionRecord]] = []
    try:
        for op in work:
            parent = op.old_path.parent
            temp = parent / f".mc-rename-{uuid.uuid4().hex}.tmp"
            while temp.exists():
                temp = parent / f".mc-rename-{uuid.uuid4().hex}.tmp"
            op.old_path.rename(temp)
            staged.append((temp, op.old_path, op.new_path, op.record))
    except OSError as e:
        for temp, old, _new, _rec in reversed(staged):
            try:
                if temp.exists():
                    temp.rename(old)
            except OSError:
                pass
        return False, f"Échec du renommage : {e}"

    completed_p2: list[tuple[Path, Path]] = []
    try:
        for temp, _old, new, _rec in staged:
            temp.rename(new)
            completed_p2.append((temp, new))
    except OSError as e:
        for _temp_p, new_p in reversed(completed_p2):
            try:
                if new_p.exists():
                    new_p.rename(_temp_p)
            except OSError:
                pass
        for temp, old, _new, _rec in reversed(staged):
            try:
                if temp.exists():
                    temp.rename(old)
            except OSError:
                pass
        return False, f"Échec du renommage : {e}"

    for _temp, _old, new, rec in staged:
        rec.output_path = new

    return True, ""
