"""
Configuration centralisée du logging pour Markdown Converter.

Politique :

- Un seul logger nommé ``markdown_converter`` (et ses enfants ``markdown_converter.<module>``).
- Niveaux exposés à l'utilisateur : **INFO / WARNING / ERROR**.
- Fichier de log persistant, par défaut macOS-natif
  (``~/Library/Logs/MarkdownConverter/run.log``), avec rotation simple
  via ``RotatingFileHandler`` (1 Mo, 5 backups).
- Un ``CallbackHandler`` permet à l'UI (ou à un outil CLI) de recevoir chaque
  message sous la forme ``(level_name, formatted_message)`` pour le rendu
  (couleur, préfixe, etc.) sans coupler le code métier au widget Tk.

L'application reste **100 % locale** : aucun handler distant n'est défini.
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Callable
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGER_NAME = "markdown_converter"
DEFAULT_MAX_BYTES = 1_000_000
DEFAULT_BACKUP_COUNT = 5

LogCallback = Callable[[str, str], None]


def _default_log_dir() -> Path:
    """
    Emplacement standard du dossier de logs.

    - macOS : ``~/Library/Logs/MarkdownConverter/`` (convention Apple,
      visible dans Console.app).
    - Autres plateformes : ``~/.markdown-converter/logs/`` (fallback).

    L'env var ``CONVERTISSEUR_LOG_DIR`` permet d'override (utile pour les tests
    et pour des cas particuliers de déploiement).
    """
    override = os.environ.get("CONVERTISSEUR_LOG_DIR")
    if override:
        return Path(override).expanduser()

    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Logs" / "MarkdownConverter"
    return home / ".markdown-converter" / "logs"


def get_log_file_path() -> Path:
    """Chemin du fichier de log principal (``run.log`` dans le dossier de logs)."""
    return _default_log_dir() / "run.log"


_already_configured = False


def setup_logging(level: int = logging.INFO) -> Path:
    """
    Initialise le logger global ``markdown_converter`` et son ``RotatingFileHandler``.

    Idempotent : peut être appelé plusieurs fois (par ``main.py``, par les
    tests, etc.). Le file handler n'est attaché qu'une seule fois pour éviter
    les logs dupliqués.

    Renvoie le chemin du fichier de log, utile pour la documentation
    utilisateur (« vos logs sont là ») et pour les tests.
    """
    global _already_configured

    log_path = get_log_file_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    if not _already_configured:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=DEFAULT_MAX_BYTES,
            backupCount=DEFAULT_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        _already_configured = True

    return log_path


def get_logger(module: str | None = None) -> logging.Logger:
    """
    Retourne ``markdown_converter`` (root applicatif) ou ``markdown_converter.<module>``.

    À utiliser dans chaque module métier : ``logger = get_logger(__name__)``.
    """
    if module:
        return logging.getLogger(f"{LOGGER_NAME}.{module}")
    return logging.getLogger(LOGGER_NAME)


class CallbackHandler(logging.Handler):
    """
    Handler qui propage chaque ``LogRecord`` à un callback applicatif.

    Le callback reçoit ``(level_name, formatted_message)`` — exactement ce
    dont l'UI a besoin pour afficher un préfixe ``[INFO]`` / ``[WARN]`` /
    ``[ERROR]`` ou colorer le widget. Le formatter par défaut n'émet que le
    message (sans timestamp/niveau) pour rester lisible dans le widget Tk.
    """

    def __init__(self, callback: LogCallback, level: int = logging.INFO):
        super().__init__(level=level)
        self._callback = callback
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self._callback(record.levelname, msg)
        except Exception:  # noqa: BLE001
            self.handleError(record)


def install_callback_handler(callback: LogCallback) -> CallbackHandler:
    """
    Installe un ``CallbackHandler`` sur le logger ``markdown_converter`` et le
    renvoie pour permettre son retrait ultérieur (``remove_callback_handler``).
    """
    handler = CallbackHandler(callback)
    get_logger().addHandler(handler)
    return handler


def remove_callback_handler(handler: CallbackHandler) -> None:
    """Retire un ``CallbackHandler`` précédemment installé. Idempotent."""
    get_logger().removeHandler(handler)
