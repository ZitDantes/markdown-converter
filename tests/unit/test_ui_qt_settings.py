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


def test_session_paths_roundtrip_and_cap(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import ui_qt_settings as m

    p = tmp_path / "settings.json"
    monkeypatch.setattr(m, "settings_path", lambda: p)
    many = [tmp_path / f"f{i}.txt" for i in range(m.SESSION_SOURCE_PATHS_LIMIT + 50)]
    m.save_session_paths_and_output(many, tmp_path)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert len(data["source_paths"]) == m.SESSION_SOURCE_PATHS_LIMIT
    loaded = m.load_source_paths()
    assert len(loaded) == m.SESSION_SOURCE_PATHS_LIMIT


def test_session_merges_theme(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import ui_qt_settings as m

    p = tmp_path / "settings.json"
    monkeypatch.setattr(m, "settings_path", lambda: p)
    m.save_theme("dark")
    m.save_session_paths_and_output([tmp_path / "a.docx"], tmp_path)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["theme"] == "dark"
    assert data["output_dir"] == str(tmp_path.resolve())


def test_load_source_paths_ignores_garbage(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import ui_qt_settings as m

    p = tmp_path / "settings.json"
    monkeypatch.setattr(m, "settings_path", lambda: p)
    p.write_text(
        '{"source_paths": ["/ok.txt", 3, "", "  /other.pdf  "]}\n',
        encoding="utf-8",
    )
    assert m.load_source_paths() == ["/ok.txt", "/other.pdf"]


def test_save_session_drops_output_dir_when_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import ui_qt_settings as m

    p = tmp_path / "settings.json"
    monkeypatch.setattr(m, "settings_path", lambda: p)
    m.save_session_paths_and_output([], tmp_path)
    m.save_session_paths_and_output([], None)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "output_dir" not in data
