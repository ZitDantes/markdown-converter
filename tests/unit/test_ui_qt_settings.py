"""Tests des chemins et de la persistance ``ui_qt_settings`` (PLO-28)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_settings_path_linux(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("MARKDOWN_CONVERTER_SETTINGS_DIR", raising=False)
    monkeypatch.setattr("platform.system", lambda: "Linux")
    import ui_qt_settings as m

    monkeypatch.setattr(
        m, "settings_path", lambda: tmp_path / ".config" / "markdown-converter" / "settings.json"
    )
    assert m.settings_path() == tmp_path / ".config" / "markdown-converter" / "settings.json"


def test_settings_path_darwin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("MARKDOWN_CONVERTER_SETTINGS_DIR", raising=False)
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    import ui_qt_settings as m

    expect = tmp_path / "Library" / "Application Support" / "Markdown Converter" / "settings.json"
    monkeypatch.setattr(m, "settings_path", lambda: expect)
    assert m.settings_path() == expect


def test_settings_path_windows(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ad = tmp_path / "Roaming"
    monkeypatch.setenv("APPDATA", str(ad))
    monkeypatch.delenv("MARKDOWN_CONVERTER_SETTINGS_DIR", raising=False)
    monkeypatch.setattr("platform.system", lambda: "Windows")
    import ui_qt_settings as m

    expect = ad / "Markdown Converter" / "settings.json"
    monkeypatch.setattr(m, "settings_path", lambda: expect)
    assert m.settings_path() == expect


def test_settings_dir_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    d = tmp_path / "cfg"
    monkeypatch.setenv("MARKDOWN_CONVERTER_SETTINGS_DIR", str(d))
    import ui_qt_settings as m

    assert m.app_settings_dir() == d.resolve()
    assert m.settings_path() == d.resolve() / "settings.json"


def test_load_save_theme_roundtrip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import ui_qt_settings as m

    p = tmp_path / "settings.json"
    monkeypatch.setattr(m, "settings_path", lambda: p)
    assert m.load_theme() == "light"
    m.save_theme("dark")
    assert m.load_theme() == "dark"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["theme"] == "dark"
    m.save_theme("light")
    assert m.load_theme() == "light"


def test_save_theme_merges_existing_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import ui_qt_settings as m

    p = tmp_path / "settings.json"
    monkeypatch.setattr(m, "settings_path", lambda: p)
    p.write_text('{"future_key": 42}\n', encoding="utf-8")
    m.save_theme("dark")
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["future_key"] == 42
    assert data["theme"] == "dark"
