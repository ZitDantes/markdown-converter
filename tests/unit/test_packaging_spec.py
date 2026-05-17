"""Tests légers du packaging PyInstaller (PLO-55)."""

from __future__ import annotations

from pathlib import Path


def test_markdown_converter_spec_requires_web_dist() -> None:
    spec = Path("MarkdownConverter.spec").read_text(encoding="utf-8")
    assert "web/dist" in spec
    assert "QtWebEngineCore" in spec
    assert "MARKDOWN_CONVERTER_UI" in spec
    assert '"web"' in spec or "'web'" in spec


def test_build_scripts_invoke_build_web() -> None:
    mac = Path("scripts/build_mac_app.sh").read_text(encoding="utf-8")
    linux = Path("scripts/build_linux_app.sh").read_text(encoding="utf-8")
    assert "build_web.sh" in mac
    assert "build_web.sh" in linux
