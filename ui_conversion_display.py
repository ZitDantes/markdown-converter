"""
Libellés et formats d'affichage partagés par l'UI Qt (sans PySide6).

``ui_qt_file_model`` importe PySide6 au chargement du module : les tests et
l'inspecteur ne peuvent pas y importer des helpers « purs » sans installer Qt.
Ce module ne dépend que de ``converter`` et ``pathlib``.
"""

from __future__ import annotations

from pathlib import Path

from converter import ConversionStatus


def file_byte_size(path: Path) -> int:
    """Taille en octets du fichier ``path`` (0 si inaccessible)."""
    try:
        return path.stat().st_size
    except OSError:
        return 0


def format_byte_size(num_bytes: int) -> str:
    """Affiche une taille en octets (o, Ko, Mo, …), aligné sur la colonne Taille."""
    if num_bytes < 0:
        return "—"
    if num_bytes == 0:
        return "0 o"
    units = ("o", "Ko", "Mo", "Go", "To")
    size = float(num_bytes)
    u = 0
    while size >= 1024.0 and u < len(units) - 1:
        size /= 1024.0
        u += 1
    if u == 0:
        return f"{int(size)} {units[u]}"
    text = f"{size:.1f}".rstrip("0").rstrip(".")
    return f"{text} {units[u]}"


def conversion_status_label_fr(status: ConversionStatus) -> str:
    """Libellé court du statut en français (table, inspecteur)."""
    mapping: dict[ConversionStatus, str] = {
        ConversionStatus.SUCCESS: "OK",
        ConversionStatus.SUCCESS_REVIEW: "OK · relire",
        ConversionStatus.SUCCESS_FALLBACK: "OK · secours",
        ConversionStatus.ERROR: "Erreur",
        ConversionStatus.UNSUPPORTED: "Non pris en charge",
        ConversionStatus.EMPTY: "Vide",
        ConversionStatus.PROCESSING: "En cours",
        ConversionStatus.QUEUED: "En attente",
    }
    return mapping.get(status, status.value)


def format_source_file_size(path: Path) -> str:
    """Taille du fichier source pour affichage dans l'UI (o, Ko, …)."""
    return format_byte_size(file_byte_size(path))
