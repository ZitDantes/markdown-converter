"""Tests variables d'environnement WebEngine (PLO-55)."""

from __future__ import annotations

import os

from ui_web_engine_env import configure_webengine_runtime_env


def test_configure_webengine_runtime_env_sets_sandbox_flags() -> None:
    for key in ("QTWEBENGINE_DISABLE_SANDBOX", "QTWEBENGINE_CHROMIUM_FLAGS"):
        os.environ.pop(key, None)
    configure_webengine_runtime_env()
    assert os.environ["QTWEBENGINE_DISABLE_SANDBOX"] == "1"
    assert "--no-sandbox" in os.environ["QTWEBENGINE_CHROMIUM_FLAGS"]
    os.environ.pop("QTWEBENGINE_DISABLE_SANDBOX", None)
    os.environ.pop("QTWEBENGINE_CHROMIUM_FLAGS", None)
