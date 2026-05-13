"""
Tests unitaires des fonctions pures de ``utils.py``.

Couvre les 5 helpers explicitement listés dans PLO-12
(``normalize_extension``, ``clean_markdown_body``, ``unique_output_md_path``,
``is_supported_path``, ``yaml_scalar_double_quoted``) plus quelques bonus
légers (``is_effectively_empty_markdown``, ``merge_file_lists``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from utils import (
    clean_markdown_body,
    is_effectively_empty_markdown,
    is_supported_path,
    merge_file_lists,
    normalize_extension,
    unique_output_md_path,
    yaml_scalar_double_quoted,
)


class TestNormalizeExtension:
    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("document.DOCX", ".docx"),
            ("rapport.Pdf", ".pdf"),
            ("notes.txt", ".txt"),
            ("README", ""),
            ("archive.tar.gz", ".gz"),
        ],
    )
    def test_returns_lowercased_suffix(self, filename: str, expected: str) -> None:
        assert normalize_extension(Path(filename)) == expected


class TestIsSupportedPath:
    def test_returns_true_for_supported_existing_file(self, tmp_path: Path) -> None:
        f = tmp_path / "note.txt"
        f.write_text("contenu")
        assert is_supported_path(f) is True

    def test_returns_false_for_unsupported_extension(self, tmp_path: Path) -> None:
        f = tmp_path / "data.xyz"
        f.write_text("contenu")
        assert is_supported_path(f) is False

    def test_returns_false_for_missing_file(self, tmp_path: Path) -> None:
        assert is_supported_path(tmp_path / "absent.txt") is False

    def test_returns_false_for_directory_with_supported_suffix(self, tmp_path: Path) -> None:
        d = tmp_path / "dossier.txt"
        d.mkdir()
        assert is_supported_path(d) is False


class TestCleanMarkdownBody:
    def test_strips_trailing_whitespace_per_line(self) -> None:
        out = clean_markdown_body("ligne 1   \nligne 2\t\n")
        assert out == "ligne 1\nligne 2"

    def test_collapses_excessive_blank_lines(self) -> None:
        out = clean_markdown_body("para 1\n\n\n\npara 2")
        assert out == "para 1\n\npara 2"

    def test_normalizes_crlf_to_lf(self) -> None:
        out = clean_markdown_body("ligne 1\r\nligne 2\r\n")
        assert "\r" not in out
        assert out == "ligne 1\nligne 2"


class TestIsEffectivelyEmptyMarkdown:
    @pytest.mark.parametrize(
        "text",
        ["", "   ", "\n\n\n", "\t  \r\n  \r\n"],
    )
    def test_returns_true_for_blank_input(self, text: str) -> None:
        assert is_effectively_empty_markdown(text) is True

    def test_returns_false_when_non_blank_characters_present(self) -> None:
        assert is_effectively_empty_markdown("# Titre\n\nun mot") is False


class TestUniqueOutputMdPath:
    def test_returns_base_path_when_not_existing(self, tmp_path: Path) -> None:
        out = unique_output_md_path(tmp_path, "note")
        assert out == tmp_path / "note.md"

    def test_suffixes_with_counter_when_collision(self, tmp_path: Path) -> None:
        (tmp_path / "note.md").write_text("existing")
        (tmp_path / "note_2.md").write_text("existing")
        out = unique_output_md_path(tmp_path, "note")
        assert out == tmp_path / "note_3.md"

    def test_sanitizes_unsafe_stem_characters(self, tmp_path: Path) -> None:
        out = unique_output_md_path(tmp_path, 'fichier/avec:caractères"interdits')
        # Caractères interdits remplacés par "_" ; le nom reste lisible.
        assert "/" not in out.name and ":" not in out.name and '"' not in out.name
        assert out.suffix == ".md"

    def test_creates_output_directory_if_missing(self, tmp_path: Path) -> None:
        target = tmp_path / "subdir" / "deep"
        out = unique_output_md_path(target, "doc")
        assert target.is_dir()
        assert out.parent == target


class TestYamlScalarDoubleQuoted:
    def test_wraps_in_double_quotes(self) -> None:
        assert yaml_scalar_double_quoted("hello") == '"hello"'

    def test_escapes_double_quote(self) -> None:
        assert yaml_scalar_double_quoted('un "mot"') == '"un \\"mot\\""'

    def test_escapes_backslash(self) -> None:
        assert yaml_scalar_double_quoted("a\\b") == '"a\\\\b"'

    def test_escapes_newline_and_carriage_return(self) -> None:
        assert yaml_scalar_double_quoted("a\nb\rc") == '"a\\nb\\rc"'


class TestMergeFileLists:
    def test_separates_supported_and_unsupported(self, tmp_path: Path) -> None:
        ok = tmp_path / "note.txt"
        ok.write_text("contenu")
        ko = tmp_path / "data.xyz"
        ko.write_text("contenu")

        supported, unsupported = merge_file_lists([ok, ko], [])
        assert supported == [ok.resolve()]
        assert unsupported == [ko.resolve()]

    def test_deduplicates_paths(self, tmp_path: Path) -> None:
        f = tmp_path / "note.txt"
        f.write_text("contenu")

        supported, _ = merge_file_lists([f, f, f.resolve()], [])
        assert supported == [f.resolve()]

    def test_walks_directory_recursively(self, tmp_path: Path) -> None:
        (tmp_path / "a.txt").write_text("x")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.html").write_text("<p>x</p>")
        (sub / "ignored.xyz").write_text("z")

        supported, _ = merge_file_lists([], [tmp_path])
        names = sorted(p.name for p in supported)
        assert names == ["a.txt", "b.html"]
