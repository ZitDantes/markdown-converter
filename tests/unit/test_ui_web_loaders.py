"""Tests du chargement UI web (PLO-46, PLO-55)."""

from __future__ import annotations

import sys

import pytest

from ui_web_loaders import bundle_resource_root, web_dist_index_path


def test_web_dist_index_path_points_to_web_dist() -> None:
    path = web_dist_index_path()
    assert path.name == "index.html"
    assert path.parent.name == "dist"
    if not getattr(sys, "frozen", False):
        assert path.parent.parent.name == "web"


def test_web_dist_index_path_when_frozen(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    fake_dist = tmp_path / "web" / "dist"
    fake_dist.mkdir(parents=True)
    (fake_dist / "index.html").write_text("<!DOCTYPE html><html></html>", encoding="utf-8")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert bundle_resource_root() == tmp_path
    assert web_dist_index_path() == fake_dist / "index.html"


@pytest.mark.skipif(
    not web_dist_index_path().is_file(),
    reason="web/dist absent — exécuter : cd web && npm ci && npm run build",
)
def test_resolve_web_index_url_when_dist_exists() -> None:
    pytest.importorskip("PySide6")
    from ui_web_loaders import resolve_web_index_url

    url = resolve_web_index_url()
    assert url.scheme() == "file"
    assert url.toLocalFile().endswith("index.html")
