"""
Moteur de conversion principal : `MarkItDown <https://github.com/microsoft/markitdown>`_.

L'import de ``markitdown`` est différé pour permettre à l'application de démarrer
même si le paquet est cassé ou manquant (le message d'erreur est alors plus
parlant qu'un ``ImportError`` brut au chargement des modules).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from engines.base import (
    ConverterEngine,
    EngineConversionError,
    EngineNotAvailableError,
)

# Extensions reconnues par MarkItDown dans ce projet (alignées sur ``utils.SUPPORTED_EXTENSIONS``).
_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {".docx", ".pptx", ".pdf", ".xlsx", ".html", ".htm", ".txt"}
)


def _load_markitdown_class() -> Any:
    """
    Import paresseux de ``MarkItDown``.

    Lève ``EngineNotAvailableError`` avec un message utilisateur en français si
    le paquet est absent ou trop ancien (Python < 3.10 / alpha 0.0.1a1).
    """
    try:
        from markitdown import MarkItDown as MarkItDownCls
    except ImportError as e:
        raise EngineNotAvailableError(
            "Impossible d'importer MarkItDown. Utilisez **Python 3.10 ou plus**, "
            "puis dans le dossier du projet :\n"
            "  pip install --upgrade pip\n"
            "  pip install --force-reinstall -r requirements.txt\n\n"
            f"Détail : {e}"
        ) from e
    return MarkItDownCls


def _extract_markdown(result: object) -> str:
    """Extrait le Markdown depuis l'objet résultat MarkItDown (compatibilité versions)."""
    for attr in ("text_content", "markdown", "md"):
        val = getattr(result, attr, None)
        if isinstance(val, str) and val.strip():
            return val
    return ""


class MarkItDownEngine(ConverterEngine):
    """Moteur principal de conversion via MarkItDown (mode local, sans plugin)."""

    name = "MarkItDown"

    @classmethod
    def is_available(cls) -> bool:
        try:
            _load_markitdown_class()
        except EngineNotAvailableError:
            return False
        return True

    def __init__(self) -> None:
        markitdown_cls = _load_markitdown_class()
        # ``enable_plugins=False`` garantit un comportement déterministe et 100 % local.
        self._engine = markitdown_cls(enable_plugins=False)

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in _SUPPORTED_EXTENSIONS

    def convert(self, path: Path) -> str:
        try:
            # ``convert_local`` est préféré (chemins locaux uniquement) ; repli pour anciennes versions.
            if hasattr(self._engine, "convert_local"):
                result = self._engine.convert_local(str(path))
            else:
                result = self._engine.convert(str(path))
        except Exception as e:
            raise EngineConversionError(f"{type(e).__name__} : {e}") from e
        return _extract_markdown(result)
