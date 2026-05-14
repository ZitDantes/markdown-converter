"""
Paramètres utilisateur pour l'UI Qt (PLO-28, PLO-29).

Fichier JSON unique : emplacement par plateforme, aligné sur **Markdown Converter**
(pas le chemin historique du handoff ``ConvertisseurMarkdownIA``).

- **Linux** : ``~/.config/markdown-converter/settings.json``
- **macOS** : ``~/Library/Application Support/Markdown Converter/settings.json``
- **Windows** : ``%APPDATA%\\Markdown Converter\\settings.json`` (dossier Roaming)

Variable optionnelle ``MARKDOWN_CONVERTER_SETTINGS_DIR`` : si définie, ce
répertoire remplace le chemin ci-dessus (tests ou installation portable).
"""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path

_SETTINGS_DIR_ENV = "MARKDOWN_CONVERTER_SETTINGS_DIR"

_THEME_KEY = "theme"
_VALID_THEMES = frozenset({"light", "dark"})


def app_settings_dir() -> Path:
    """Répertoire de configuration (créé à la sauvegarde si besoin)."""
    override = (os.environ.get(_SETTINGS_DIR_ENV) or "").strip()
    if override:
        return Path(override).expanduser().resolve()
    system = platform.system()
    home = Path.home()
    if system == "Windows":
        base = os.environ.get("APPDATA") or str(home / "AppData" / "Roaming")
        return Path(base) / "Markdown Converter"
    if system == "Darwin":
        return home / "Library" / "Application Support" / "Markdown Converter"
    return home / ".config" / "markdown-converter"


def settings_path() -> Path:
    """Chemin absolu du fichier ``settings.json``."""
    return app_settings_dir() / "settings.json"


def load_theme() -> str:
    """Lit la clé ``theme`` ; retourne ``light`` ou ``dark`` (défaut ``light``)."""
    path = settings_path()
    if not path.is_file():
        return "light"
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError, TypeError):
        return "light"
    if not isinstance(data, dict):
        return "light"
    t = data.get(_THEME_KEY, "light")
    return t if t in _VALID_THEMES else "light"


def save_theme(theme: str) -> None:
    """Enregistre ``theme`` (``light`` ou ``dark``), en fusionnant le JSON existant."""
    if theme not in _VALID_THEMES:
        return
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {}
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                payload = dict(existing)
        except (OSError, json.JSONDecodeError, TypeError):
            payload = {}
    payload[_THEME_KEY] = theme
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
