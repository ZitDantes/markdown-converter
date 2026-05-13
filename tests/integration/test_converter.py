"""
Tests d'intégration de ``converter.convert_files``.

Hors scope (PLO-12) : mocks de MarkItDown / Pandoc, formats binaires (.docx, .pdf,
.pptx, .xlsx). Ces cas seront ajoutés dans des tickets dédiés.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from converter import ConversionStatus, convert_files


def test_converts_simple_txt_to_markdown(tmp_path: Path, fixtures_dir: Path) -> None:
    """Cas nominal : un .txt minimal produit un .md non vide avec statut SUCCESS."""
    src = tmp_path / "simple.txt"
    shutil.copy(fixtures_dir / "simple.txt", src)
    output_dir = tmp_path / "out"

    callbacks: list[tuple[str, str]] = []
    summary = convert_files(
        explicit_files=[src],
        directory_roots=[],
        output_dir=output_dir,
        on_log=lambda level, message: callbacks.append((level, message)),
    )

    assert len(summary.records) == 1
    record = summary.records[0]
    assert record.status is ConversionStatus.SUCCESS
    assert record.output_path is not None
    assert record.output_path.exists()
    assert record.output_path.suffix == ".md"

    content = record.output_path.read_text(encoding="utf-8")
    assert content.startswith("---")  # front-matter YAML
    assert "fichier_source" in content
    assert content.strip() != ""

    # Au moins un message INFO a circulé via le callback (preuve de chaînage logger ↔ UI).
    assert any(level == "INFO" for level, _ in callbacks)


def test_unsupported_extension_yields_unsupported_record(tmp_path: Path) -> None:
    """Cas dégradé : une extension inconnue produit un record UNSUPPORTED + warning."""
    bad = tmp_path / "data.xyz"
    bad.write_text("contenu", encoding="utf-8")
    output_dir = tmp_path / "out"

    callbacks: list[tuple[str, str]] = []
    summary = convert_files(
        explicit_files=[bad],
        directory_roots=[],
        output_dir=output_dir,
        on_log=lambda level, message: callbacks.append((level, message)),
    )

    # Le fichier n'est pas converti : il apparaît dans unsupported_skipped
    # et n'engendre pas de record SUCCESS.
    resolved = bad.resolve()
    assert resolved in summary.unsupported_skipped
    assert all(r.status is not ConversionStatus.SUCCESS for r in summary.records)

    # Aucun .md ne doit avoir été créé.
    md_files = list(output_dir.glob("*.md"))
    assert md_files == []

    # L'utilisateur a bien reçu un avertissement.
    assert any(level == "WARNING" for level, _ in callbacks)
