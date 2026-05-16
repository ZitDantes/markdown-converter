"""Tests du spike WebEngine (PLO-44)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_SPIKE_DIR = Path(__file__).resolve().parents[2] / "spike" / "webengine"


def test_static_file_assets_exist() -> None:
    for name in ("index.html", "app.js", "style.css"):
        assert (_SPIKE_DIR / "static_file" / name).is_file()


def test_resources_rc_generated() -> None:
    assert (_SPIKE_DIR / "resources_rc.py").is_file()


@pytest.mark.parametrize("mode", ["file", "qrc"])
def test_resolve_page_url(mode: str) -> None:
    pytest.importorskip("PySide6")
    from spike.webengine.loaders import LoaderMode, resolve_page_url

    url = resolve_page_url(LoaderMode(mode))
    assert url.isValid()
    if mode == "file":
        assert url.scheme() == "file"
        assert url.toLocalFile().endswith("index.html")
    else:
        assert url.scheme() == "qrc"


def test_spike_bridge_ping() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from spike.webengine.bridge import SpikeBridge

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    bridge = SpikeBridge()
    bridge.set_loader_label("test")
    assert bridge.ping("  hello  ") == "pong:hello"
    assert bridge.loaderLabel() == "test"
    del app
