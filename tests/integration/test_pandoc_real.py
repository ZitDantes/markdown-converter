"""
Tests d'intégration **réels** de ``engines.pandoc_engine``.

Contrairement aux tests unitaires (``tests/unit/test_pandoc_engine.py``) qui
stubent ``subprocess.run``, ceux-ci appellent le **vrai** binaire ``pandoc``.

Ils sont automatiquement **skip** si Pandoc n'est pas dans le PATH. En CI, le
workflow ``.github/workflows/ci.yml`` installe Pandoc avant ``pytest`` pour
garantir leur exécution.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from engines.pandoc_engine import PandocEngine

pytestmark = pytest.mark.skipif(
    shutil.which("pandoc") is None,
    reason="Pandoc absent du PATH — tests d'intégration sautés (installer pandoc pour les exécuter).",
)


def test_real_pandoc_converts_html_fixture(fixtures_dir: Path) -> None:
    """
    Le vrai binaire Pandoc convertit ``tests/fixtures/simple.html`` en Markdown
    non vide contenant le titre et au moins un item de la liste.

    Ce test garantit que :

    - ``PandocEngine().convert()`` produit un Markdown exploitable sur un format
      qui sert régulièrement de secours derrière MarkItDown ;
    - le pipeline ``shutil.which → subprocess.run → stdout`` est cohérent end-to-end
      (et pas seulement avec des mocks).
    """
    src = fixtures_dir / "simple.html"
    assert src.exists(), "fixture manquante"

    output = PandocEngine().convert(src)

    assert output.strip() != ""
    assert "Page de test" in output
    assert "Premier item" in output


def test_real_pandoc_is_available() -> None:
    """``is_available()`` reflète la disponibilité réelle quand le binaire est là."""
    assert PandocEngine.is_available() is True
    assert PandocEngine.executable_path() is not None
