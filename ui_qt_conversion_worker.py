"""
Worker Qt qui exécute ``converter.convert_files`` dans un ``QThread`` (PLO-35).

Conception :

- Le worker est un ``QObject`` qui s'auto-suffit ; il est destiné à être déplacé
  dans un ``QThread`` via ``moveToThread`` et démarré par le signal ``started``
  du thread connecté à ``run()``.
- ``use_conversion_fallback`` (défaut ``True``) : transmis à ``convert_files`` (PLO-40).
- Les callbacks ``on_log`` / ``on_progress`` de ``convert_files`` sont
  **transformés en signaux Qt** : l'UI ne reçoit donc jamais d'appel direct
  depuis le thread worker, ce qui respecte le modèle de threading Qt et évite
  les corruptions d'arbre de widgets.
- Le résultat (``ConversionSummary``) est émis via ``finished``. Une exception
  inattendue est captée et émise via ``failed`` (message texte uniquement, pour
  ne pas faire fuiter d'objet entre threads).

Comme pour ``ui_qt.py`` et ``ui_qt_file_model.py``, on évite d'importer Qt au
plus haut niveau si possible — ici on l'importe au module car ce fichier n'est
sollicité **qu'à partir** de l'UI Qt active.
"""

from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from converter import ConversionSummary, convert_files


class ConversionWorker(QObject):
    """Exécute ``convert_files`` et relaie ses callbacks en signaux Qt."""

    progress = Signal(int, int, str, float)
    log = Signal(str, str)
    finished = Signal(ConversionSummary)
    failed = Signal(str)

    def __init__(
        self,
        explicit_files: list[Path],
        directory_roots: list[Path],
        output_dir: Path,
        *,
        keep_output_in_memory: bool = True,
        use_conversion_fallback: bool = True,
    ) -> None:
        super().__init__()
        self._explicit_files = list(explicit_files)
        self._directory_roots = list(directory_roots)
        self._output_dir = output_dir
        self._keep_output_in_memory = keep_output_in_memory
        self._use_conversion_fallback = use_conversion_fallback

    def run(self) -> None:
        """Slot à connecter à ``QThread.started``. Exécution synchrone dans le thread."""
        try:
            summary = convert_files(
                self._explicit_files,
                self._directory_roots,
                self._output_dir,
                on_log=self._emit_log,
                on_progress=self._emit_progress,
                keep_output_in_memory=self._keep_output_in_memory,
                use_conversion_fallback=self._use_conversion_fallback,
            )
        except Exception as exc:  # noqa: BLE001 — on relaie texte uniquement
            self.failed.emit(f"{type(exc).__name__} : {exc}\n{traceback.format_exc()}")
            return
        self.finished.emit(summary)

    def _emit_log(self, level: str, message: str) -> None:
        self.log.emit(level, message)

    def _emit_progress(self, index: int, total: int, label: str, percent: float) -> None:
        self.progress.emit(index, total, label, percent)
