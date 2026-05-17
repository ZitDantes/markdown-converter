"""Variables d'environnement Qt WebEngine (dev + bundle PyInstaller, PLO-55)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _executable_dir() -> Path:
    return Path(sys.executable).resolve().parent


def _find_qt_webengine_framework() -> Path | None:
    """Localise ``QtWebEngineCore.framework`` dans un bundle macOS ou onedir."""
    exe_dir = _executable_dir()
    candidates = [
        exe_dir.parent / "Frameworks" / "PySide6" / "Qt" / "lib" / "QtWebEngineCore.framework",
        exe_dir / "PySide6" / "Qt" / "lib" / "QtWebEngineCore.framework",
    ]
    for path in candidates:
        if path.is_dir():
            return path
    for path in exe_dir.parent.rglob("QtWebEngineCore.framework"):
        if path.is_dir():
            return path
    return None


def _configure_frozen_webengine_paths() -> None:
    """
    Définit ``QTWEBENGINEPROCESS_PATH`` et ressources si PyInstaller a mal rangé le framework.

    Sans cela, le .app macOS quitte immédiatement (processus Chromium introuvable).
    """
    if not getattr(sys, "frozen", False):
        return

    framework = _find_qt_webengine_framework()
    if framework is None:
        return

    if not os.environ.get("QTWEBENGINEPROCESS_PATH"):
        for proc in framework.rglob("QtWebEngineProcess"):
            if proc.is_file() and proc.name == "QtWebEngineProcess":
                os.environ["QTWEBENGINEPROCESS_PATH"] = os.fspath(proc.resolve())
                break

    if not os.environ.get("QTWEBENGINE_RESOURCES_PATH"):
        for icu in framework.rglob("icudtl.dat"):
            if icu.is_file():
                res_dir = icu.parent.resolve()
                os.environ["QTWEBENGINE_RESOURCES_PATH"] = os.fspath(res_dir)
                locales = res_dir / "qtwebengine_locales"
                if locales.is_dir():
                    os.environ.setdefault(
                        "QTWEBENGINE_LOCALES_PATH",
                        os.fspath(locales.resolve()),
                    )
                break


def configure_webengine_runtime_env() -> None:
    """
    À appeler avant tout import/utilisation de Qt WebEngine.

    Dans une app PyInstaller, le sandbox Chromium ne trouve pas toujours
    ``QtWebEngineProcess`` → abort dans ``WebContentsAdapter`` au lancement.
    """
    os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
    flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "").strip()
    if "--no-sandbox" not in flags.split():
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = f"{flags} --no-sandbox".strip()
    _configure_frozen_webengine_paths()
