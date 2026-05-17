"""Tests réparation QtWebEngineCore.framework (packaging macOS)."""

from __future__ import annotations

import os
from pathlib import Path

from webengine_macos_repair import repair_qt_webengine_framework
from ui_web_engine_env import configure_webengine_runtime_env


def test_repair_copies_helpers_and_resources_to_version_a(tmp_path: Path) -> None:
    fw = tmp_path / "QtWebEngineCore.framework"
    stray = fw / "Versions" / "Resources"
    a_dir = fw / "Versions" / "A"
    stray.mkdir(parents=True)
    a_dir.mkdir(parents=True)
    (stray / "Helpers" / "QtWebEngineProcess.app" / "Contents" / "MacOS").mkdir(
        parents=True
    )
    (stray / "Helpers" / "QtWebEngineProcess.app" / "Contents" / "MacOS" / "QtWebEngineProcess").write_bytes(
        b"x"
    )
    (stray / "Resources").mkdir(parents=True)
    (stray / "Resources" / "icudtl.dat").write_bytes(b"icu")
    (stray / "Resources" / "qtwebengine_locales").mkdir()
    (stray / "Resources" / "qtwebengine_locales" / "en-US.pak").write_bytes(b"pak")

    assert repair_qt_webengine_framework(fw) is True
    assert (a_dir / "Helpers" / "QtWebEngineProcess.app").is_dir()
    assert (a_dir / "Resources" / "icudtl.dat").is_file()


def test_configure_frozen_paths_from_framework(tmp_path: Path, monkeypatch) -> None:
    import sys

    app = tmp_path / "Markdown Converter.app"
    fw = (
        app
        / "Contents"
        / "Frameworks"
        / "PySide6"
        / "Qt"
        / "lib"
        / "QtWebEngineCore.framework"
    )
    proc = (
        fw
        / "Versions"
        / "Resources"
        / "Helpers"
        / "QtWebEngineProcess.app"
        / "Contents"
        / "MacOS"
        / "QtWebEngineProcess"
    )
    res = fw / "Versions" / "Resources" / "Resources"
    proc.parent.mkdir(parents=True)
    proc.write_bytes(b"p")
    res.mkdir(parents=True)
    (res / "icudtl.dat").write_bytes(b"i")
    (res / "qtwebengine_locales").mkdir()
    (res / "qtwebengine_locales" / "en-US.pak").write_bytes(b"l")

    exe = app / "Contents" / "MacOS" / "Markdown Converter"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe), raising=False)
    for key in (
        "QTWEBENGINEPROCESS_PATH",
        "QTWEBENGINE_RESOURCES_PATH",
        "QTWEBENGINE_LOCALES_PATH",
    ):
        os.environ.pop(key, None)

    configure_webengine_runtime_env()
    assert os.environ["QTWEBENGINEPROCESS_PATH"] == os.fspath(proc.resolve())
    assert Path(os.environ["QTWEBENGINE_RESOURCES_PATH"]) == res.resolve()
    assert Path(os.environ["QTWEBENGINE_LOCALES_PATH"]) == (res / "qtwebengine_locales").resolve()
