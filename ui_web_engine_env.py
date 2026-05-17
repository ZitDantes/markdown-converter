"""Variables d'environnement Qt WebEngine (dev + bundle PyInstaller, PLO-55)."""

from __future__ import annotations

import os


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
