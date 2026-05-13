"""Tests du parseur de front-matter ``ui_qt_inspector_data`` (PLO-38)."""

from __future__ import annotations

from ui_qt_inspector_data import FrontMatterParseResult, parse_front_matter
from utils import yaml_scalar_double_quoted


def _build(front: dict[str, str], body: str) -> str:
    lines = ["---"]
    for k, v in front.items():
        lines.append(f"{k}: {yaml_scalar_double_quoted(v)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body


def test_parse_minimal_block() -> None:
    text = _build(
        {
            "titre": "Rapport",
            "fichier_source": "/tmp/a.pdf",
            "date_conversion": "2026-05-13 22:00:00",
        },
        "# Rapport\n\nCorps.\n",
    )
    result = parse_front_matter(text)
    assert isinstance(result, FrontMatterParseResult)
    assert result.front_matter["titre"] == "Rapport"
    assert result.front_matter["fichier_source"] == "/tmp/a.pdf"
    assert result.front_matter["date_conversion"] == "2026-05-13 22:00:00"
    assert "# Rapport" in result.body
    assert result.body.endswith("Corps.\n")
    assert result.raw_front_matter.startswith("---\n")
    assert result.raw_front_matter.endswith("---\n")


def test_parse_with_warning() -> None:
    text = _build(
        {
            "titre": "Doc",
            "fichier_source": "x",
            "date_conversion": "y",
            "avertissement": "À relire : conversion approximative.",
        },
        "Corps.\n",
    )
    result = parse_front_matter(text)
    assert "avertissement" in result.front_matter
    assert result.front_matter["avertissement"].startswith("À relire")


def test_unescape_special_chars() -> None:
    text = _build(
        {"titre": 'un "titre" avec \\ et \nretour'},
        "Corps.\n",
    )
    result = parse_front_matter(text)
    assert result.front_matter["titre"] == 'un "titre" avec \\ et \nretour'


def test_no_front_matter_returns_text_as_body() -> None:
    text = "# Sans front-matter\n\nCorps libre."
    result = parse_front_matter(text)
    assert result.front_matter == {}
    assert result.body == text
    assert result.raw_front_matter == ""


def test_unclosed_block_returns_text_as_body() -> None:
    text = '---\ntitre: "Sans fermeture"\n\n# Corps.'
    result = parse_front_matter(text)
    assert result.front_matter == {}
    assert result.body == text


def test_empty_input() -> None:
    result = parse_front_matter("")
    assert result.front_matter == {}
    assert result.body == ""


def test_ignores_blank_and_malformed_lines() -> None:
    text = (
        "---\n"
        "\n"
        'titre: "OK"\n'
        "ligne sans deux-points ignoree\n"
        ": valeur sans cle ignoree\n"
        "---\n\nCorps."
    )
    result = parse_front_matter(text)
    assert result.front_matter == {"titre": "OK"}
    assert result.body.endswith("Corps.")


def test_unknown_escape_is_preserved_defensively() -> None:
    text = '---\ntitre: "a\\zb"\n---\n\nCorps.'
    result = parse_front_matter(text)
    assert result.front_matter["titre"] == "a\\zb"
