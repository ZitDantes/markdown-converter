"""
Disponibilité de l'UI web (PLO-54) — détection avant lancement et messages en français.

Politique de repli (``main.py``) lorsque ``MARKDOWN_CONVERTER_UI=web`` :

- Par défaut : interface **Qt widgets** (``ui_qt``, parité fonctionnelle).
- ``MARKDOWN_CONVERTER_WEB_FALLBACK=tk`` : interface Tkinter.
- ``MARKDOWN_CONVERTER_WEB_FALLBACK=none`` : message d'erreur puis sortie (code 1).
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from enum import Enum


class WebUiBlockReason(str, Enum):
    """Cause d'indisponibilité de l'UI web embarquée."""

    PYSIDE6_MISSING = "pyside6_missing"
    WEBENGINE_MISSING = "webengine_missing"
    WEB_DIST_MISSING = "web_dist_missing"


@dataclass(frozen=True)
class WebUiAvailability:
    """Résultat de la sonde locale (aucun appel réseau)."""

    ok: bool
    reason: WebUiBlockReason | None = None
    detail: str | None = None


def probe_web_ui_availability() -> WebUiAvailability:
    """Vérifie PySide6, Qt WebEngine et la présence de ``web/dist/index.html``."""
    if importlib.util.find_spec("PySide6.QtWidgets") is None:
        return WebUiAvailability(
            ok=False,
            reason=WebUiBlockReason.PYSIDE6_MISSING,
            detail="module PySide6.QtWidgets introuvable",
        )

    if importlib.util.find_spec("PySide6.QtWebEngineWidgets") is None:
        return WebUiAvailability(
            ok=False,
            reason=WebUiBlockReason.WEBENGINE_MISSING,
            detail="module PySide6.QtWebEngineWidgets introuvable",
        )

    try:
        from ui_web_loaders import web_dist_index_path

        if not web_dist_index_path().is_file():
            raise FileNotFoundError(web_dist_index_path())
    except FileNotFoundError as exc:
        return WebUiAvailability(
            ok=False,
            reason=WebUiBlockReason.WEB_DIST_MISSING,
            detail=str(exc),
        )

    return WebUiAvailability(ok=True)


def format_web_unavailable_message(avail: WebUiAvailability) -> str:
    """Message actionnable pour stderr / logs (français)."""
    if avail.ok:
        return ""

    lines = ["L'interface web (Qt WebEngine) n'est pas disponible.", ""]

    if avail.reason is WebUiBlockReason.PYSIDE6_MISSING:
        lines.extend(
            [
                "PySide6 est introuvable.",
                "  pip install -r requirements-qt.txt",
                "",
                "Ou lancez une autre interface :",
                "  MARKDOWN_CONVERTER_UI=qt python3 main.py",
                "  MARKDOWN_CONVERTER_UI=tk python3 main.py",
            ]
        )
    elif avail.reason is WebUiBlockReason.WEBENGINE_MISSING:
        lines.extend(
            [
                "Le module Qt WebEngineWidgets est introuvable.",
                "Installez les dépendances système (Linux) puis réinstallez PySide6 si besoin.",
                "Voir : spike/webengine/README.md (section dépendances Linux).",
                "",
                "Exemple Debian/Ubuntu :",
                "  sudo apt-get install -y libnss3 libnspr4 libatk-bridge2.0-0 \\",
                "    libcups2 libdrm2 libgbm1 libxcomposite1 libxdamage1 libxfixes3 \\",
                "    libxrandr2 libpango-1.0-0 libcairo2 libasound2",
                "",
                "Bascule automatique vers l'interface Qt widgets (par défaut) ou :",
                "  MARKDOWN_CONVERTER_WEB_FALLBACK=tk",
                "  MARKDOWN_CONVERTER_WEB_FALLBACK=none   # arrêt sans repli",
            ]
        )
    elif avail.reason is WebUiBlockReason.WEB_DIST_MISSING:
        lines.extend(
            [
                "Le build front ``web/dist/index.html`` est absent.",
                "  ./scripts/build_web.sh",
                "  # ou : cd web && npm ci && npm run build",
            ]
        )
    else:
        lines.append("Raison inconnue.")

    if avail.detail:
        lines.extend(["", f"Détail : {avail.detail}"])

    return "\n".join(lines)


def ensure_web_ui_ready() -> None:
    """Quitte le processus (code 1) si l'UI web ne peut pas démarrer."""
    import sys

    avail = probe_web_ui_availability()
    if not avail.ok:
        print(format_web_unavailable_message(avail), file=sys.stderr)
        raise SystemExit(1)
