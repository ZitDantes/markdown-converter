"""
Configuration commune à tous les tests pytest.

Rôles :

- Isoler les logs : chaque test pointe ``CONVERTISSEUR_LOG_DIR`` vers un dossier
  temporaire pour ne **jamais** écrire dans ``~/Library/Logs/...`` pendant les
  tests, et pour permettre l'inspection du fichier produit dans certains tests.
- Exposer ``FIXTURES_DIR`` pour les tests qui consomment les petits documents
  versionnés dans ``tests/fixtures/``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _isolated_log_dir(tmp_path_factory, monkeypatch):
    """
    Reproduit le démarrage applicatif (``main.py``) pour les tests :

    - redirige ``CONVERTISSEUR_LOG_DIR`` vers un dossier jetable ;
    - réinitialise le flag idempotent de ``logging_setup`` pour repartir
      d'un logger propre à chaque test ;
    - appelle ``setup_logging()`` afin que le logger ``convertisseur`` ait
      bien son niveau **INFO** (sinon les ``logger.info`` du métier sont
      filtrés et les callbacks UI ne reçoivent rien).
    """
    log_dir = tmp_path_factory.mktemp("logs")
    monkeypatch.setenv("CONVERTISSEUR_LOG_DIR", str(log_dir))
    import logging_setup

    monkeypatch.setattr(logging_setup, "_already_configured", False, raising=False)
    logging_setup.setup_logging()
    return log_dir


@pytest.fixture
def fixtures_dir() -> Path:
    """Chemin du dossier ``tests/fixtures/`` (documents minimaux versionnés)."""
    return FIXTURES_DIR
