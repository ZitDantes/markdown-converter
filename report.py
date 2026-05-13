"""
Génération du fichier ``rapport_conversion.md`` après un lot de conversions.
"""

from __future__ import annotations

from pathlib import Path

from converter import ConversionStatus, ConversionSummary


def write_report(summary: ConversionSummary, report_path: Path | None = None) -> Path:
    """
    Écrit le rapport dans ``summary.output_dir / rapport_conversion.md``
    (ou ``report_path`` si fourni).
    """
    out = report_path or (summary.output_dir / "rapport_conversion.md")
    lines: list[str] = []

    lines.append("# Rapport de conversion")
    lines.append("")
    lines.append("Ce rapport a été généré automatiquement par **Markdown Converter**.")
    lines.append("")
    lines.append("## Résumé")
    lines.append("")
    success = [r for r in summary.records if r.status == ConversionStatus.SUCCESS]
    errors = [r for r in summary.records if r.status == ConversionStatus.ERROR]
    empty = [r for r in summary.records if r.status == ConversionStatus.EMPTY]
    lines.append(f"- **Début du lot** : {summary.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **Fin du lot** : {summary.finished_at.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **Dossier de sortie** : `{summary.output_dir}`")
    lines.append(f"- **Fichiers convertis avec succès** : {len(success)}")
    lines.append(f"- **Fichiers en erreur** : {len(errors)}")
    lines.append(f"- **Fichiers vides (non écrits)** : {len(empty)}")
    lines.append(
        f"- **Chemins ignorés (format non supporté)** : {len(summary.unsupported_skipped)}"
    )
    lines.append(
        f"- **Pandoc disponible sur la machine** : {'oui' if summary.pandoc_available else 'non'}"
    )
    lines.append("")

    lines.append("## Relecture obligatoire pour certains formats")
    lines.append("")
    lines.append(
        "Les fichiers **PDF** et **PPTX** issus de conversion automatique peuvent contenir "
        "des erreurs d'ordre des blocs, des pertes de mise en page ou des approximations sur "
        "les tableaux et les images. **Ils doivent être relus par un humain** avant d'être "
        "intégrés tels quels dans une base de connaissances ou un système RAG."
    )
    lines.append("")

    lines.append("## Fichiers convertis avec succès")
    lines.append("")
    if not success:
        lines.append("_Aucun._")
    else:
        for r in success:
            out_name = r.output_path.name if r.output_path else "?"
            pandoc_note = " (secours Pandoc)" if r.used_pandoc_fallback else ""
            lines.append(f"- `{r.source_path}` → `{out_name}`{pandoc_note}")
            if r.message:
                lines.append(f"  - Note : {r.message}")
    lines.append("")

    lines.append("## Fichiers en erreur")
    lines.append("")
    if not errors:
        lines.append("_Aucun._")
    else:
        for r in errors:
            lines.append(f"- `{r.source_path}`")
            if r.error_type:
                lines.append(f"  - **Type d'erreur** : `{r.error_type}`")
            lines.append(f"  - {r.message or 'Erreur inconnue.'}")
    lines.append("")

    lines.append("## Fichiers vides (aucun Markdown produit)")
    lines.append("")
    if not empty:
        lines.append("_Aucun._")
    else:
        for r in empty:
            type_note = f" (type : `{r.error_type}`)" if r.error_type else ""
            lines.append(f"- `{r.source_path}`{type_note} : {r.message or 'Contenu vide.'}")
    lines.append("")

    lines.append("## Formats non supportés (ignorés)")
    lines.append("")
    if not summary.unsupported_skipped:
        lines.append("_Aucun._")
    else:
        for p in summary.unsupported_skipped:
            lines.append(f"- `{p}`")
    lines.append("")

    lines.append("## Avertissements et traces")
    lines.append("")
    if not summary.warnings:
        lines.append("_Aucun avertissement._")
    else:
        for w in summary.warnings:
            lines.append(w)
            lines.append("")

    text = "\n".join(lines).rstrip() + "\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out
