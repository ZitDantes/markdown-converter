"""
Utilitaires : extensions supportées, collecte de fichiers, nettoyage Markdown,
chemins de sortie uniques et avertissements par format.

Les helpers spécifiques à Pandoc ont été déplacés dans ``engines/pandoc_engine.py``.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

# Extensions traitées par le convertisseur (minuscules)
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {".docx", ".pptx", ".pdf", ".xlsx", ".html", ".htm", ".txt"}
)

# Formats pour lesquels un avertissement de relecture est recommandé
REVIEW_RECOMMENDED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".pptx"})


def normalize_extension(path: Path) -> str:
    """Retourne l'extension en minuscules (ex. ``.DOCX`` -> ``.docx``)."""
    return path.suffix.lower()


def is_supported_path(path: Path) -> bool:
    return path.is_file() and normalize_extension(path) in SUPPORTED_EXTENSIONS


def collect_supported_files_under_directory(root: Path) -> list[Path]:
    """Parcourt ``root`` récursivement et retourne les fichiers aux formats supportés."""
    out: list[Path] = []
    if not root.is_dir():
        return out
    for p in root.rglob("*"):
        if p.is_file() and is_supported_path(p):
            out.append(p.resolve())
    return sorted(out)


def merge_file_lists(
    explicit_files: Iterable[Path],
    directory_roots: Iterable[Path],
) -> tuple[list[Path], list[Path]]:
    """
    Fusionne fichiers explicites et contenu des dossiers (récursif).

    Retourne ``(fichiers_supportés_uniques, chemins_non_supportés_ignorés)``.
    Les doublons (même chemin résolu) sont supprimés.
    """
    seen: set[Path] = set()
    supported: list[Path] = []
    unsupported: list[Path] = []

    def add_path(p: Path) -> None:
        p = p.resolve()
        if p in seen:
            return
        seen.add(p)
        if not p.exists():
            return
        if p.is_file():
            ext = normalize_extension(p)
            if ext in SUPPORTED_EXTENSIONS:
                supported.append(p)
            else:
                unsupported.append(p)

    for f in explicit_files:
        add_path(f)

    for d in directory_roots:
        d = d.resolve()
        if not d.exists():
            continue
        if d.is_file():
            add_path(d)
            continue
        for child in collect_supported_files_under_directory(d):
            add_path(child)

    return supported, unsupported


def unique_output_md_path(output_dir: Path, source_stem: str) -> Path:
    """
    Retourne un chemin ``output_dir / {stem}.md`` sans écraser un fichier existant
    (suffixes ``_2``, ``_3``, ...).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    base = _safe_stem(source_stem)
    candidate = output_dir / f"{base}.md"
    n = 2
    while candidate.exists():
        candidate = output_dir / f"{base}_{n}.md"
        n += 1
    return candidate


def _safe_stem(stem: str) -> str:
    """Évite les noms de fichier problématiques ; garde un maximum de lisibilité."""
    s = stem.strip() or "document"
    # Remplace caractères interdits / déconseillés sur les systèmes de fichiers
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", s)
    s = s.rstrip(" .")
    return s or "document"


def collapse_blank_lines(text: str, max_consecutive_blank: int = 2) -> str:
    """Réduit les suites de lignes vides (garde au plus ``max_consecutive_blank`` newlines)."""
    lines = text.splitlines()
    out: list[str] = []
    blank_run = 0
    for line in lines:
        if line.strip() == "":
            blank_run += 1
            if blank_run <= max_consecutive_blank:
                out.append("")
        else:
            blank_run = 0
            out.append(line.rstrip())
    return "\n".join(out).strip("\n")


def clean_markdown_body(text: str) -> str:
    """Supprime espaces superflus en fin de ligne et compresse les blancs verticaux."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = collapse_blank_lines(text, max_consecutive_blank=1)
    return text.strip()


def is_effectively_empty_markdown(text: str) -> bool:
    """Vrai si, après nettoyage, il ne reste aucun caractère non blanc."""
    return clean_markdown_body(text).strip() == ""


def format_warning_for_extension(ext: str) -> str | None:
    """Message d'avertissement standard selon le format (ou ``None``)."""
    ext = ext.lower()
    if ext in REVIEW_RECOMMENDED_EXTENSIONS:
        return (
            "La conversion automatique peut être incomplète ou réordonnancer le contenu. "
            "Une relecture humaine est fortement recommandée avant usage en base de connaissances."
        )
    if ext == ".xlsx":
        return (
            "Les classeurs Excel sont convertis en texte/Markdown : formules, mise en forme "
            "et graphiques peuvent être perdus ou simplifiés."
        )
    if ext in {".html", ".htm"}:
        return "Le rendu dépend de la structure HTML : scripts et styles ne sont pas reproduits à l'identique."
    return None


def yaml_scalar_double_quoted(value: str) -> str:
    """Encode une chaîne pour YAML en style double guillemets (échappement minimal)."""
    escaped = (
        value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
    )
    return f'"{escaped}"'
