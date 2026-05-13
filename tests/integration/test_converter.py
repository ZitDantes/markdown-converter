"""
Tests d'intégration de ``converter.convert_files``.

Hors scope : conversion réelle de formats binaires (.docx, .pdf, .pptx, .xlsx).
Pour les transitions de statut côté secours, on monkeypatche les engines de
``converter`` afin de ne pas dépendre de la présence de Pandoc en CI.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from converter import ConversionStatus, convert_files


def test_output_md_text_none_by_default(tmp_path: Path, fixtures_dir: Path) -> None:
    """Par défaut (``keep_output_in_memory=False``), aucun corps n'est conservé en RAM."""
    src = tmp_path / "simple.txt"
    shutil.copy(fixtures_dir / "simple.txt", src)
    output_dir = tmp_path / "out"

    summary = convert_files(
        explicit_files=[src],
        directory_roots=[],
        output_dir=output_dir,
    )

    record = summary.records[0]
    assert record.output_md_text is None
    assert record.output_path is not None and record.output_path.exists()


def test_output_md_text_captured_when_option_enabled(
    tmp_path: Path,
    fixtures_dir: Path,
) -> None:
    """Avec ``keep_output_in_memory=True``, le record contient exactement le contenu écrit."""
    src = tmp_path / "simple.txt"
    shutil.copy(fixtures_dir / "simple.txt", src)
    output_dir = tmp_path / "out"

    summary = convert_files(
        explicit_files=[src],
        directory_roots=[],
        output_dir=output_dir,
        keep_output_in_memory=True,
    )

    record = summary.records[0]
    assert record.output_path is not None
    assert record.output_md_text is not None
    assert record.output_md_text.startswith("---")
    assert record.output_md_text == record.output_path.read_text(encoding="utf-8")


def test_output_md_text_only_for_successful_records(tmp_path: Path) -> None:
    """Les records non-SUCCESS (ici UNSUPPORTED) n'ont jamais d'``output_md_text``."""
    bad = tmp_path / "data.xyz"
    bad.write_text("contenu", encoding="utf-8")
    output_dir = tmp_path / "out"

    summary = convert_files(
        explicit_files=[bad],
        directory_roots=[],
        output_dir=output_dir,
        keep_output_in_memory=True,
    )

    assert all(r.output_md_text is None for r in summary.records)


def test_on_progress_percent_monotonic_and_records_finished(
    tmp_path: Path,
    fixtures_dir: Path,
) -> None:
    """Le 4e argument ``percent`` est non décroissant ; aucun record ne reste en PROCESSING."""
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    shutil.copy(fixtures_dir / "simple.txt", a)
    shutil.copy(fixtures_dir / "simple.txt", b)
    output_dir = tmp_path / "out"

    percents: list[float] = []

    def on_progress(_i: int, _t: int, _lab: str, pct: float) -> None:
        percents.append(pct)

    summary = convert_files(
        explicit_files=[a, b],
        directory_roots=[],
        output_dir=output_dir,
        on_progress=on_progress,
    )

    assert percents, "au moins une notification de progression attendue"
    assert percents == sorted(percents)
    assert percents[-1] == pytest.approx(1.0)
    assert all(r.status is not ConversionStatus.PROCESSING for r in summary.records)
    assert all(r.progress_percent == pytest.approx(1.0) for r in summary.records)


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


def test_converts_simple_html_to_markdown(tmp_path: Path, fixtures_dir: Path) -> None:
    """Cas HTML : conversion OK, statut SUCCESS_REVIEW car le format a un avertissement."""
    src = tmp_path / "simple.html"
    shutil.copy(fixtures_dir / "simple.html", src)
    output_dir = tmp_path / "out"

    summary = convert_files(
        explicit_files=[src],
        directory_roots=[],
        output_dir=output_dir,
    )

    assert len(summary.records) == 1
    record = summary.records[0]
    # HTML déclenche format_warning_for_extension → SUCCESS_REVIEW (pas SUCCESS pur).
    assert record.status is ConversionStatus.SUCCESS_REVIEW
    assert record.output_path is not None
    assert record.output_path.exists()

    content = record.output_path.read_text(encoding="utf-8")
    assert content.startswith("---")  # front-matter YAML
    # Le titre et au moins un item de la liste doivent survivre à la conversion HTML.
    assert "Page de test" in content
    assert "Premier item" in content


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


def test_success_fallback_when_primary_fails_and_pandoc_recovers(
    tmp_path: Path,
    fixtures_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Si le moteur primaire lève ``EngineConversionError`` et que le secours
    réussit, le statut doit être ``SUCCESS_FALLBACK`` (et non ``SUCCESS``).

    On utilise un fichier ``.txt`` (pas d'avertissement de format) pour
    distinguer ``SUCCESS_FALLBACK`` de ``SUCCESS_REVIEW``.
    """
    import converter
    from engines import EngineConversionError

    class _BrokenPrimary:
        name = "FakeMarkItDown"

        @classmethod
        def is_available(cls) -> bool:
            return True

        def supports(self, path: Path) -> bool:
            return True

        def convert(self, src: Path) -> str:
            raise EngineConversionError("simulated primary failure")

    class _GoodFallback:
        name = "FakePandoc"

        @classmethod
        def is_available(cls) -> bool:
            return True

        @classmethod
        def executable_path(cls) -> str:
            return "/fake/pandoc"

        def supports(self, path: Path) -> bool:
            return True

        def convert(self, src: Path) -> str:
            return "# Contenu récupéré\n\nLe secours a fonctionné."

    monkeypatch.setattr(converter, "MarkItDownEngine", _BrokenPrimary)
    monkeypatch.setattr(converter, "PandocEngine", _GoodFallback)

    src = tmp_path / "simple.txt"
    shutil.copy(fixtures_dir / "simple.txt", src)
    output_dir = tmp_path / "out"

    summary = convert_files(
        explicit_files=[src],
        directory_roots=[],
        output_dir=output_dir,
    )

    assert len(summary.records) == 1
    record = summary.records[0]
    assert record.status is ConversionStatus.SUCCESS_FALLBACK
    assert record.used_pandoc_fallback is True
    assert record.engine_used == "FakePandoc"
    assert record.output_path is not None and record.output_path.exists()
