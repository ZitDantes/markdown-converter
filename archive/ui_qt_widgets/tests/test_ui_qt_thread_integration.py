"""
Tests d'intégration UI Qt (PLO-31) : ``QThread`` + boucle d'événements.

On exécute le chemin réel ``MarkdownConverterQtApp._on_convert_clicked`` (worker
``moveToThread``, connexions ``QueuedConnection``) tout en remplaçant
``convert_files`` par un faux qui émet ``on_progress`` / ``on_log`` depuis le
thread worker. Le thread principal pompe les événements : la barre de
progression et le modèle doivent se mettre à jour sans blocage ni crash.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest


def _pump_until_worker_idle(app: object, *, timeout_s: float = 8.0) -> None:
    """Attend que ``_worker_thread`` repasse à ``None`` (slot ``_clear_worker_refs``)."""
    from PySide6.QtWidgets import QApplication

    deadline = time.perf_counter() + timeout_s
    while time.perf_counter() < deadline:
        QApplication.processEvents()
        if getattr(app, "_worker_thread", None) is None:
            return
        time.sleep(0.002)
    pytest.fail(f"timeout : le worker Qt n'a pas libéré le thread sous {timeout_s} s")


def test_convert_flow_mocked_engine_updates_ui_from_worker_thread(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    pytest.importorskip("PySide6", reason="PySide6 requis pour ce test d'intégration")

    import os
    import sys

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    import ui_qt_conversion_worker as worker_mod
    from converter import ConversionStatus, ConversionSummary, FileConversionRecord
    from ui_qt import MarkdownConverterQtApp, add_paths_to_model

    main_ident = threading.main_thread().ident

    def fake_convert(
        explicit_files: list[Path],
        directory_roots: list[Path],
        output_dir: Path,
        on_log: object = None,
        on_progress: object = None,
        *,
        keep_output_in_memory: bool = True,
        use_conversion_fallback: bool = True,
    ) -> ConversionSummary:
        assert threading.current_thread().ident != main_ident, (
            "convert_files mockée doit s'exécuter hors du thread UI"
        )
        assert explicit_files
        _ = directory_roots
        _ = keep_output_in_memory
        _ = use_conversion_fallback
        if on_log:
            on_log("INFO", "mock conversion démarrée")
        if on_progress:
            on_progress(0, 1, "Étape fictive", 0.25)
        time.sleep(0.02)
        if on_progress:
            on_progress(0, 1, "Étape fictive", 0.75)
        time.sleep(0.02)
        if on_progress:
            on_progress(0, 1, "Étape fictive", 1.0)
        now = datetime.now(timezone.utc)
        out_md = output_dir / f"{explicit_files[0].stem}.md"
        rec = FileConversionRecord(
            source_path=explicit_files[0].resolve(),
            status=ConversionStatus.SUCCESS,
            output_path=out_md,
            progress_percent=1.0,
        )
        return ConversionSummary(
            started_at=now,
            finished_at=now,
            output_dir=output_dir.resolve(),
            records=[rec],
            pandoc_available=False,
        )

    monkeypatch.setattr(worker_mod, "convert_files", fake_convert)

    qapp = QApplication.instance() or QApplication(sys.argv)

    out_dir = tmp_path / "sortie"
    out_dir.mkdir()
    src = tmp_path / "note.txt"
    src.write_text("hello", encoding="utf-8")

    app = MarkdownConverterQtApp()
    app.build()
    assert app.file_view_parts is not None and app.footer_parts is not None

    add_paths_to_model(app.file_view_parts.model, [src])
    app.set_output_dir(out_dir)

    max_bar = 0

    def sample_bar() -> None:
        nonlocal max_bar
        max_bar = max(max_bar, app.footer_parts.progress_bar.value())

    tick = QTimer(qapp)
    tick.setInterval(4)
    tick.timeout.connect(sample_bar)
    tick.start()

    app._on_convert_clicked()
    _pump_until_worker_idle(app, timeout_s=8.0)
    tick.stop()
    qapp.processEvents()
    sample_bar()

    assert max_bar >= 25, "la barre doit refléter une progression intermédiaire (≥ 25 %)"
    assert app.footer_parts.progress_bar.value() == 100
    assert "Terminé" in app.footer_parts.status_label.text()
    records = app.file_view_parts.model.records()
    assert len(records) == 1
    assert records[0].status == ConversionStatus.SUCCESS
