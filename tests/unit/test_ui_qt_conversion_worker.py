"""
Tests du worker Qt ``ConversionWorker`` (PLO-35).

On exécute ``run()`` **synchroneusement** dans le thread principal pour ne pas
dépendre de pytest-qt. Cela suffit à vérifier :

- les signaux ``progress`` et ``log`` sont émis (au moins une fois pour un
  fichier non vide) ;
- ``finished`` reçoit bien un ``ConversionSummary`` correct.

Le câblage concret ``QThread + moveToThread`` est couvert par le smoke offscreen
de la CI ; le faire ici nécessiterait ``QApplication.exec()`` et un timeout.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def qt_app() -> object:
    pytest.importorskip("PySide6", reason="PySide6 non installé localement")
    import os
    import sys

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def test_worker_emits_finished_with_summary(qt_app: object, tmp_path: Path) -> None:
    from converter import ConversionStatus, ConversionSummary
    from ui_qt_conversion_worker import ConversionWorker

    source = tmp_path / "exemple.txt"
    source.write_text("Bonjour le monde", encoding="utf-8")
    output_dir = tmp_path / "out"

    progress_calls: list[tuple[int, int, str, float]] = []
    log_calls: list[tuple[str, str]] = []
    finished: list[ConversionSummary] = []
    failed: list[str] = []

    worker = ConversionWorker(
        explicit_files=[source],
        directory_roots=[],
        output_dir=output_dir,
        keep_output_in_memory=True,
    )
    worker.progress.connect(lambda i, t, lab, p: progress_calls.append((i, t, lab, p)))
    worker.log.connect(lambda lvl, msg: log_calls.append((lvl, msg)))
    worker.finished.connect(finished.append)
    worker.failed.connect(failed.append)

    worker.run()

    assert failed == []
    assert len(finished) == 1
    summary = finished[0]
    assert isinstance(summary, ConversionSummary)
    assert len(summary.records) == 1
    record = summary.records[0]
    assert record.source_path == source.resolve()
    assert record.status in {
        ConversionStatus.SUCCESS,
        ConversionStatus.SUCCESS_REVIEW,
        ConversionStatus.SUCCESS_FALLBACK,
    }
    assert progress_calls, "au moins un signal progress attendu"
    assert log_calls, "au moins un signal log attendu (info Pandoc dispo/indispo)"
