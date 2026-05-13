"""
Moteur de conversion de secours : `Pandoc <https://pandoc.org/>`_.

Le moteur n'est utilisé qu'en repli si MarkItDown échoue ou produit un Markdown
vide. Il dépend d'un exécutable ``pandoc`` présent dans le ``PATH`` ; sans cela,
``is_available()`` renvoie ``False`` et l'orchestrateur n'instancie pas la classe.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from engines.base import (
    ConverterEngine,
    EngineConversionError,
    EngineNotAvailableError,
)

# Mapping extension → nom du lecteur ``--from=`` de Pandoc.
_PANDOC_FORMAT_MAP: dict[str, str] = {
    ".docx": "docx",
    ".pptx": "pptx",
    ".pdf": "pdf",
    ".html": "html",
    ".htm": "html",
    ".txt": "plain",
}


def _find_pandoc() -> str | None:
    """Chemin vers l'exécutable ``pandoc`` si présent sur le système."""
    return shutil.which("pandoc")


class PandocEngine(ConverterEngine):
    """Moteur de secours via l'exécutable Pandoc."""

    name = "Pandoc"

    @classmethod
    def is_available(cls) -> bool:
        return _find_pandoc() is not None

    @classmethod
    def executable_path(cls) -> str | None:
        """Chemin vers l'exécutable Pandoc, ou ``None`` si non installé."""
        return _find_pandoc()

    def __init__(self) -> None:
        exe = _find_pandoc()
        if exe is None:
            raise EngineNotAvailableError(
                "Pandoc n'est pas installé ou absent du PATH. "
                "Installez-le via « brew install pandoc » (macOS) "
                "ou voir https://pandoc.org/installing.html ."
            )
        self._pandoc_exe = exe

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in _PANDOC_FORMAT_MAP

    def convert(self, path: Path) -> str:
        ext = path.suffix.lower()
        reader = _PANDOC_FORMAT_MAP.get(ext)
        if not reader:
            raise EngineConversionError(
                f"Pandoc ne propose pas de lecteur adapté pour ce format "
                f"({ext or 'sans extension'})."
            )
        cmd = [
            self._pandoc_exe,
            f"--from={reader}",
            "--to=gfm",
            "--standalone",
            str(path),
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            raise EngineConversionError(err or f"Pandoc a échoué (code {proc.returncode}).")
        return proc.stdout
