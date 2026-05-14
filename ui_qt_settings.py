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

_SOURCE_PATHS_KEY = "source_paths"
_OUTPUT_DIR_KEY = "output_dir"

# Plafond pour éviter un JSON disproportionné (file très longue, dossiers massifs).
SESSION_SOURCE_PATHS_LIMIT = 100


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


def _read_json_object() -> dict[str, object]:
    path = settings_path()
    if not path.is_file():
        return {}
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def load_theme() -> str:
    """Lit la clé ``theme`` ; retourne ``light`` ou ``dark`` (défaut ``light``)."""
    data = _read_json_object()
    t = data.get(_THEME_KEY, "light")
    return t if t in _VALID_THEMES else "light"


def load_source_paths() -> list[str]:
    """Chemins sources enregistrés (fichiers), ordre conservé, longueur plafonnée."""
    data = _read_json_object()
    raw = data.get(_SOURCE_PATHS_KEY, [])
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
        if len(out) >= SESSION_SOURCE_PATHS_LIMIT:
            break
    return out


def load_output_dir_str() -> str | None:
    """Chemin dossier de sortie enregistré, ou ``None`` si absent / invalide."""
    data = _read_json_object()
    v = data.get(_OUTPUT_DIR_KEY)
    if isinstance(v, str) and v.strip():
        return v.strip()
    return None


def _write_merged_payload(updates: dict[str, object]) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _read_json_object()
    payload.update(updates)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_theme(theme: str) -> None:
    """Enregistre ``theme`` (``light`` ou ``dark``), en fusionnant le JSON existant."""
    if theme not in _VALID_THEMES:
        return
    _write_merged_payload({_THEME_KEY: theme})


def save_session_paths_and_output(source_paths: list[Path], output_dir: Path | None) -> None:
    """Enregistre la file (chemins résolus, plafonnés) et le dossier de sortie."""
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _read_json_object()
    capped = source_paths[:SESSION_SOURCE_PATHS_LIMIT]
    payload[_SOURCE_PATHS_KEY] = [str(p.resolve()) for p in capped]
    if output_dir is not None:
        payload[_OUTPUT_DIR_KEY] = str(output_dir.resolve())
    else:
        payload.pop(_OUTPUT_DIR_KEY, None)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
