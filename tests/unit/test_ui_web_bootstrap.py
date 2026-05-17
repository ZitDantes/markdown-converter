"""Tests disponibilité UI web et politique de repli (PLO-54)."""

from __future__ import annotations

import os

import pytest

from ui_web_bootstrap import (
    WebUiBlockReason,
    format_web_unavailable_message,
    probe_web_ui_availability,
)


def test_probe_ok_when_web_stack_available(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("PySide6")
    from pathlib import Path

    index = Path(__file__).resolve().parents[2] / "web" / "dist" / "index.html"
    if not index.is_file():
        pytest.skip("web/dist absent — lancer ./scripts/build_web.sh")

    avail = probe_web_ui_availability()
    assert avail.ok is True


def test_probe_web_dist_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("PySide6")
    from pathlib import Path

    fake = Path("/tmp/markdown-converter-missing-web-dist/index.html")

    def _fake_path() -> Path:
        return fake

    monkeypatch.setattr("ui_web_loaders.web_dist_index_path", _fake_path)
    avail = probe_web_ui_availability()
    assert avail.ok is False
    assert avail.reason is WebUiBlockReason.WEB_DIST_MISSING
    msg = format_web_unavailable_message(avail)
    assert "web/dist" in msg
    assert "build_web" in msg


def test_format_webengine_message_actionable() -> None:
    from ui_web_bootstrap import WebUiAvailability

    msg = format_web_unavailable_message(
        WebUiAvailability(ok=False, reason=WebUiBlockReason.WEBENGINE_MISSING)
    )
    assert "WebEngine" in msg
    assert "MARKDOWN_CONVERTER_WEB_FALLBACK" in msg
    assert "spike/webengine/README.md" in msg


def test_resolve_web_fallback_env() -> None:
    from main import (
        WEB_FALLBACK_ENV,
        WEB_FALLBACK_NONE,
        WEB_FALLBACK_TK,
        _resolve_web_fallback,
    )

    os.environ[WEB_FALLBACK_ENV] = "tk"
    assert _resolve_web_fallback() == WEB_FALLBACK_TK
    os.environ[WEB_FALLBACK_ENV] = "none"
    assert _resolve_web_fallback() == WEB_FALLBACK_NONE
    os.environ[WEB_FALLBACK_ENV] = "qt"
    assert _resolve_web_fallback() == WEB_FALLBACK_TK
    del os.environ[WEB_FALLBACK_ENV]
    assert _resolve_web_fallback() == WEB_FALLBACK_TK
