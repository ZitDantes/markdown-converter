"""
Logique de conversion : MarkItDown en priorité, Pandoc en secours si disponible.
"""

from __future__ import annotations

import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from utils import (
    SUPPORTED_EXTENSIONS,
    clean_markdown_body,
    find_pandoc,
    format_warning_for_extension,
    is_effectively_empty_markdown,
    merge_file_lists,
    normalize_extension,
    pandoc_from_format_for_extension,
    run_pandoc_to_markdown,
    unique_output_md_path,
    yaml_scalar_double_quoted,
)


def _load_markitdown_class() -> Any:
    """
    Import paresseux de MarkItDown (évite l'échec au chargement du module si le paquet est absent).

    Les versions récentes (PyPI, Python 3.10+) exposent ``MarkItDown`` ; l'alpha 0.0.1a1 sous Python 3.9 non.
    """
    try:
        from markitdown import MarkItDown as MarkItDownCls
    except ImportError as e:
        raise RuntimeError(
            "Impossible d'importer MarkItDown. Utilisez **Python 3.10 ou plus**, puis dans le dossier du projet :\n"
            "  pip install --upgrade pip\n"
            "  pip install --force-reinstall -r requirements.txt\n\n"
            f"Détail : {e}"
        ) from e
    return MarkItDownCls


class ConversionStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    UNSUPPORTED = "unsupported"
    EMPTY = "empty"


@dataclass
class FileConversionRecord:
    """Résultat pour un fichier source."""

    source_path: Path
    status: ConversionStatus
    output_path: Path | None = None
    message: str | None = None
    used_pandoc_fallback: bool = False


@dataclass
class ConversionSummary:
    """Synthèse d'un lot de conversions."""

    started_at: datetime
    finished_at: datetime
    output_dir: Path
    records: list[FileConversionRecord] = field(default_factory=list)
    unsupported_skipped: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    pandoc_available: bool = False


LogFn = Callable[[str], None]
ProgressFn = Callable[[int, int, str], None]


def _markdown_from_markitdown_result(result: object) -> str:
    """Extrait le texte Markdown depuis l'objet résultat MarkItDown (compatibilité versions)."""
    for attr in ("text_content", "markdown", "md"):
        val = getattr(result, attr, None)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def _infer_title_from_body(stem: str, body: str) -> str:
    """Titre : première ligne ``# ...`` si présente, sinon nom de fichier sans extension."""
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip() or stem
    return stem


def _build_front_matter(
    titre: str,
    fichier_source: str,
    date_conversion: str,
    avertissement: str | None,
) -> str:
    lines = [
        "---",
        f"titre: {yaml_scalar_double_quoted(titre)}",
        f"fichier_source: {yaml_scalar_double_quoted(fichier_source)}",
        f"date_conversion: {yaml_scalar_double_quoted(date_conversion)}",
    ]
    if avertissement:
        lines.append(f"avertissement: {yaml_scalar_double_quoted(avertissement)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def _convert_with_markitdown(md_engine: Any, path: Path) -> str:
    # ``convert_local`` est préféré (chemins locaux uniquement) ; repli pour anciennes versions.
    if hasattr(md_engine, "convert_local"):
        result = md_engine.convert_local(str(path))
    else:
        result = md_engine.convert(str(path))
    return _markdown_from_markitdown_result(result)


def _try_pandoc(path: Path, pandoc_exe: str) -> str:
    ext = normalize_extension(path)
    reader = pandoc_from_format_for_extension(ext)
    if not reader:
        raise RuntimeError("Pandoc ne propose pas de lecteur adapté pour ce format.")
    return run_pandoc_to_markdown(pandoc_exe, path, reader)


def convert_files(
    explicit_files: list[Path],
    directory_roots: list[Path],
    output_dir: Path,
    on_log: LogFn | None = None,
    on_progress: ProgressFn | None = None,
) -> ConversionSummary:
    """
    Convertit une liste de fichiers et/ou l'arborescence de dossiers vers ``output_dir``.

    ``on_log`` reçoit des messages en français ; ``on_progress(index, total, label)``.
    """
    started = datetime.now()
    log = on_log or (lambda _m: None)
    prog = on_progress or (lambda _i, _t, _l: None)

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    pandoc_exe = find_pandoc()
    pandoc_ok = bool(pandoc_exe)
    if not pandoc_ok:
        log(
            "Note : Pandoc n'est pas installé ou absent du PATH. "
            "La conversion utilise **uniquement MarkItDown**, ce qui est le fonctionnement normal du programme. "
            "Pandoc est **optionnel** : il sert de secours si un fichier pose problème avec MarkItDown. "
            "Pour l'ajouter : « brew install pandoc » (macOS) ou voir https://pandoc.org/installing.html ."
        )
    else:
        log(
            f"Pandoc est disponible ({pandoc_exe}) ; il ne sera utilisé qu'en secours si MarkItDown échoue "
            "ou renvoie un contenu vide."
        )

    supported, unsupported = merge_file_lists(explicit_files, directory_roots)
    summary = ConversionSummary(
        started_at=started,
        finished_at=started,
        output_dir=output_dir,
        unsupported_skipped=list(unsupported),
        pandoc_available=pandoc_ok,
    )

    for p in unsupported:
        ext = normalize_extension(p)
        msg = f"Ignoré (format non supporté « {ext or '(sans extension)'} ») : {p}"
        log(msg)
        summary.warnings.append(msg)

    total = len(supported)
    if total == 0:
        log("Aucun fichier à convertir : ajoutez des fichiers ou un dossier contenant des formats supportés.")
        summary.finished_at = datetime.now()
        return summary

    MarkItDown = _load_markitdown_class()
    md_engine = MarkItDown(enable_plugins=False)

    for idx, src in enumerate(supported, start=1):
        label = src.name
        prog(idx - 1, total, label)
        ext = normalize_extension(src)
        if ext not in SUPPORTED_EXTENSIONS:
            summary.records.append(
                FileConversionRecord(
                    source_path=src,
                    status=ConversionStatus.UNSUPPORTED,
                    message="Extension non reconnue.",
                )
            )
            continue

        fmt_warning = format_warning_for_extension(ext)
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            body = _convert_with_markitdown(md_engine, src)
            body = clean_markdown_body(body)
            used_pandoc = False

            if is_effectively_empty_markdown(body) and pandoc_ok:
                try:
                    body = clean_markdown_body(_try_pandoc(src, pandoc_exe))  # type: ignore[arg-type]
                    used_pandoc = True
                except Exception as pe:  # noqa: BLE001
                    log(f"Pandoc (secours) n'a pas pu convertir « {src.name} » : {pe}")

            if is_effectively_empty_markdown(body):
                msg = (
                    "Le document converti est vide après nettoyage. "
                    "Le fichier Markdown n'a pas été créé pour éviter un fichier vide."
                )
                log(f"Échec pour « {src.name} » : {msg}")
                summary.records.append(
                    FileConversionRecord(
                        source_path=src,
                        status=ConversionStatus.EMPTY,
                        message=msg,
                    )
                )
                summary.warnings.append(f"{src} : {msg}")
                continue

            titre = _infer_title_from_body(src.stem, body)
            header = _build_front_matter(
                titre=titre,
                fichier_source=str(src),
                date_conversion=date_str,
                avertissement=fmt_warning,
            )
            final_md = header + body + "\n"

            out_path = unique_output_md_path(output_dir, src.stem)
            out_path.write_text(final_md, encoding="utf-8")

            summary.records.append(
                FileConversionRecord(
                    source_path=src,
                    status=ConversionStatus.SUCCESS,
                    output_path=out_path,
                    used_pandoc_fallback=used_pandoc,
                )
            )
            how = "Pandoc (secours)" if used_pandoc else "MarkItDown"
            log(f"OK — « {src.name} » → « {out_path.name} » ({how}).")

        except Exception as e:  # noqa: BLE001
            tb = traceback.format_exc()
            human = f"{type(e).__name__} : {e}"
            log(f"Erreur pour « {src.name} » : {human}")

            if pandoc_ok:
                try:
                    body = clean_markdown_body(_try_pandoc(src, pandoc_exe))  # type: ignore[arg-type]
                    if not is_effectively_empty_markdown(body):
                        titre = _infer_title_from_body(src.stem, body)
                        header = _build_front_matter(
                            titre=titre,
                            fichier_source=str(src),
                            date_conversion=date_str,
                            avertissement=fmt_warning,
                        )
                        out_path = unique_output_md_path(output_dir, src.stem)
                        out_path.write_text(header + body + "\n", encoding="utf-8")
                        summary.records.append(
                            FileConversionRecord(
                                source_path=src,
                                status=ConversionStatus.SUCCESS,
                                output_path=out_path,
                                used_pandoc_fallback=True,
                                message="Conversion réussie via Pandoc après échec de MarkItDown.",
                            )
                        )
                        log(f"Récupéré par Pandoc — « {src.name} » → « {out_path.name} ».")
                        continue
                except Exception as pe:  # noqa: BLE001
                    log(f"Pandoc (secours) a également échoué pour « {src.name} » : {pe}")

            summary.records.append(
                FileConversionRecord(
                    source_path=src,
                    status=ConversionStatus.ERROR,
                    message=human,
                )
            )
            summary.warnings.append(f"Trace technique pour « {src} » :\n```\n{tb}\n```")

        prog(idx, total, label)

    summary.finished_at = datetime.now()
    return summary
