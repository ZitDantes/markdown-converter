"""Tests du chargement UI web (PLO-46)."""

from __future__ import annotations

import pytest

from ui_web_loaders import web_dist_index_path


def test_web_dist_index_path_points_to_web_dist() -> None:
    path = web_dist_index_path()
    assert path.name == "index.html"
    assert path.parent.name == "dist"
    assert path.parent.parent.name == "web"


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
