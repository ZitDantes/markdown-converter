"""
Shell PySide6 + WebEngine pour l'UI web (PLO-46).

Charge ``web/dist/index.html`` et expose ``WebBackend`` via QWebChannel (ADR 0001).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QFileDialog, QMainWindow, QWidget

from bridge_contract import (
    BACKEND_OBJECT_NAME,
    AckResult,
    ClearQueueResult,
    ConversionFinishedEvent,
    PickFilesResult,
    PickFolderResult,
    QueueState,
    SetOutputDirResult,
    StartConversionCommand,
    file_queue_item_from_record,
    summary_dto_from_summary,
)
from bridge_contract.models import progress_event_from_worker
from converter import ConversionStatus, ConversionSummary, FileConversionRecord
from ui_qt import add_paths_to_model
from ui_qt_file_model import ConversionFileTableModel
from ui_web_loaders import resolve_web_index_url
from utils import SUPPORTED_EXTENSIONS, collect_supported_files_under_directory, is_supported_path


def _validate_output_dir(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "Le dossier n'existe pas."
    if not path.is_dir():
        return False, "Le chemin désigné n'est pas un dossier."
    if not os.access(path, os.W_OK):
        return False, "Ce dossier n'est pas accessible en écriture."
    return True, ""


class _QueueModel:
    """File en mémoire (même sémantique que ``ConversionFileTableModel`` sans Qt)."""

    def __init__(self) -> None:
        self._records: list[FileConversionRecord] = []

    def records(self) -> list[FileConversionRecord]:
        return self._records

    def set_records(self, records: list[FileConversionRecord]) -> None:
        self._records = list(records)

    def clear(self) -> int:
        n = len(self._records)
        self._records.clear()
        return n


class WebBackend(QObject):
    """Objet QWebChannel ``backend`` (contrat v0)."""

    logEmitted = Signal(str, str)
    progressUpdated = Signal(str)
    queueUpdated = Signal(str)
    conversionFinished = Signal(str)
    conversionFailed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._parent_widget = parent
        self._queue = _QueueModel()
        self._output_dir: Path | None = None
        self._worker_thread: QThread | None = None
        self._worker: object | None = None
        self._worker_sink: _WorkerBridgeSink | None = None
        self._emit_queue_updated()

    @Slot(str, result=str)
    def ping(self, message: str) -> str:
        text = (message or "").strip()
        return f"pong:{text or 'vide'}"

    @Slot(result=str)
    def pickFiles(self) -> str:
        pattern = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))
        paths, _ = QFileDialog.getOpenFileNames(
            self._parent_widget,
            "Ajouter des fichiers",
            "",
            f"Documents pris en charge ({pattern})",
        )
        if not paths:
            return json.dumps(PickFilesResult(cancelled=True).to_dict(), ensure_ascii=False)
        added = self._add_paths([Path(p) for p in paths])
        return json.dumps(
            PickFilesResult(paths=[str(p) for p in added], cancelled=False).to_dict(),
            ensure_ascii=False,
        )

    @Slot(result=str)
    def pickOutputDir(self) -> str:
        folder = QFileDialog.getExistingDirectory(
            self._parent_widget,
            "Choisir le dossier de sortie",
        )
        if not folder:
            return json.dumps(
                SetOutputDirResult(ok=False, errorMessage="Annulé").to_dict(),
                ensure_ascii=False,
            )
        return self.setOutputDir(folder)

    @Slot(result=str)
    def pickFolder(self) -> str:
        folder = QFileDialog.getExistingDirectory(self._parent_widget, "Ajouter un dossier")
        if not folder:
            return json.dumps(PickFolderResult(cancelled=True).to_dict(), ensure_ascii=False)
        paths = collect_supported_files_under_directory(Path(folder))
        self._add_paths(paths)
        return json.dumps(
            PickFolderResult(path=folder, cancelled=False).to_dict(),
            ensure_ascii=False,
        )

    @Slot(str, result=str)
    def setOutputDir(self, path: str) -> str:
        target = Path(path).expanduser()
        ok, err = _validate_output_dir(target)
        if not ok:
            return json.dumps(
                SetOutputDirResult(ok=False, errorMessage=err).to_dict(),
                ensure_ascii=False,
            )
        self._output_dir = target.resolve()
        self._emit_queue_updated()
        return json.dumps(
            SetOutputDirResult(ok=True, outputDir=str(self._output_dir)).to_dict(),
            ensure_ascii=False,
        )

    @Slot(result=str)
    def getQueueState(self) -> str:
        return self._queue_state_json()

    @Slot(result=str)
    def clearQueue(self) -> str:
        n = self._queue.clear()
        self._emit_queue_updated()
        return json.dumps(ClearQueueResult(clearedCount=n).to_dict(), ensure_ascii=False)

    @Slot(str, result=str)
    def removeQueueItem(self, source_path: str) -> str:
        if self._worker_thread is not None:
            return json.dumps(
                AckResult(ok=False, message="Conversion en cours — action impossible.").to_dict(),
                ensure_ascii=False,
            )
        target = Path(source_path)
        records = [r for r in self._queue.records() if r.source_path != target]
        if len(records) == len(self._queue.records()):
            return json.dumps(
                AckResult(ok=False, message="Fichier introuvable dans la file.").to_dict(),
                ensure_ascii=False,
            )
        self._queue.set_records(records)
        self._emit_queue_updated()
        return json.dumps(AckResult(ok=True).to_dict(), ensure_ascii=False)

    @Slot(str, result=str)
    def startConversion(self, command_json: str) -> str:
        if self._worker_thread is not None:
            return json.dumps(
                AckResult(ok=False, message="Une conversion est déjà en cours.").to_dict(),
                ensure_ascii=False,
            )
        if self._output_dir is None:
            return json.dumps(
                AckResult(ok=False, message="Choisissez un dossier de sortie.").to_dict(),
                ensure_ascii=False,
            )
        paths = [rec.source_path for rec in self._queue.records()]
        if not paths:
            return json.dumps(
                AckResult(ok=False, message="La file est vide.").to_dict(),
                ensure_ascii=False,
            )

        cmd = StartConversionCommand.from_json(command_json)
        self._start_worker(
            paths, self._output_dir, use_conversion_fallback=cmd.useConversionFallback
        )
        self.logEmitted.emit("INFO", f"Conversion démarrée ({len(paths)} fichier(s))…")
        self._emit_queue_updated()
        return json.dumps(AckResult(ok=True).to_dict(), ensure_ascii=False)

    @Slot(result=str)
    def cancelConversion(self) -> str:
        return json.dumps(
            AckResult(ok=False, message="Annulation non implémentée (v0).").to_dict(),
            ensure_ascii=False,
        )

    def _add_paths(self, paths: list[Path]) -> list[Path]:
        """Ajoute des chemins supportés ; réutilise ``add_paths_to_model`` via adaptateur."""
        model = ConversionFileTableModel(self._queue.records())
        added = add_paths_to_model(model, paths)
        self._queue.set_records(model.records())
        self._emit_queue_updated()
        return added

    def _queue_state_json(self) -> str:
        from ui_conversion_display import file_byte_size, format_byte_size

        records = self._queue.records()
        items = [file_queue_item_from_record(r) for r in records]
        total_bytes = sum(file_byte_size(r.source_path) for r in records)
        can_start = (
            self._output_dir is not None
            and bool(items)
            and self._worker_thread is None
            and all(is_supported_path(r.source_path) for r in records)
        )
        state = QueueState(
            items=items,
            outputDir=str(self._output_dir) if self._output_dir else None,
            canStartConversion=can_start,
            totalSizeLabel=format_byte_size(total_bytes),
        )
        return json.dumps(state.to_dict(), ensure_ascii=False)

    def _emit_queue_updated(self) -> None:
        self.queueUpdated.emit(self._queue_state_json())

    def _start_worker(
        self,
        paths: list[Path],
        output_dir: Path,
        *,
        use_conversion_fallback: bool,
    ) -> None:
        from ui_qt_conversion_worker import ConversionWorker

        # Référence forte obligatoire (cf. ui_qt._worker_ui_sink) — sinon GC PySide6 coupe les signaux.
        self._worker_sink = _WorkerBridgeSink(self)
        sink = self._worker_sink
        worker = ConversionWorker(
            explicit_files=paths,
            directory_roots=[],
            output_dir=output_dir,
            keep_output_in_memory=True,
            use_conversion_fallback=use_conversion_fallback,
        )
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.log.connect(sink.on_log, Qt.ConnectionType.QueuedConnection)
        worker.progress.connect(sink.on_progress, Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(sink.on_finished, Qt.ConnectionType.QueuedConnection)
        worker.failed.connect(sink.on_failed, Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_worker)

        self._worker = worker
        self._worker_thread = thread
        thread.start()

    def _clear_worker(self) -> None:
        self._worker = None
        self._worker_thread = None
        self._worker_sink = None
        self._emit_queue_updated()

    def _apply_progress(self, index: int, total: int, label: str, percent: float) -> None:
        records = self._queue.records()
        if total <= 0 or not records:
            return
        row = index if index < len(records) else len(records) - 1
        rec = records[row]
        rec.progress_percent = max(0.0, min(1.0, percent * total - row))
        if rec.status == ConversionStatus.QUEUED:
            rec.status = ConversionStatus.PROCESSING
        event = progress_event_from_worker(index, total, label, percent)
        self.progressUpdated.emit(json.dumps(event.to_dict(), ensure_ascii=False))
        self._emit_queue_updated()

    def _apply_finished(self, summary: object) -> None:
        if not isinstance(summary, ConversionSummary):
            self.logEmitted.emit("ERROR", "Résumé de conversion invalide.")
            return
        self._queue.set_records(list(summary.records))
        dto = summary_dto_from_summary(summary)
        event = ConversionFinishedEvent(summary=dto)
        from converter import SUCCESS_STATUSES, ConversionStatus

        ok = sum(1 for r in summary.records if r.status in SUCCESS_STATUSES)
        err = sum(1 for r in summary.records if r.status == ConversionStatus.ERROR)
        self.logEmitted.emit(
            "INFO",
            f"Conversion terminée : {ok} réussi(s), {err} erreur(s).",
        )
        self.conversionFinished.emit(json.dumps(event.to_dict(), ensure_ascii=False))
        self._emit_queue_updated()

    def _apply_failed(self, message: str) -> None:
        first = message.splitlines()[0] if message else "Échec de la conversion."
        self.conversionFailed.emit(first)


class _WorkerBridgeSink(QObject):
    """Relais worker → signaux ``WebBackend`` (thread GUI uniquement)."""

    def __init__(self, backend: WebBackend) -> None:
        super().__init__(backend)
        self._backend = backend

    @Slot(str, str)
    def on_log(self, level: str, message: str) -> None:
        self._backend.logEmitted.emit(level, message)

    @Slot(int, int, str, float)
    def on_progress(self, index: int, total: int, label: str, percent: float) -> None:
        self._backend._apply_progress(index, total, label, percent)

    @Slot(object)
    def on_finished(self, summary: object) -> None:
        self._backend._apply_finished(summary)

    @Slot(str)
    def on_failed(self, error_text: str) -> None:
        self._backend._apply_failed(error_text)


def _configure_web_settings(view: QWebEngineView) -> None:
    from PySide6.QtWebEngineCore import QWebEngineSettings

    settings = view.page().settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)


def _register_web_channel(view: QWebEngineView, backend: WebBackend) -> None:
    from PySide6.QtWebChannel import QWebChannel

    channel = QWebChannel(view.page())
    channel.registerObject(BACKEND_OBJECT_NAME, backend)
    view.page().setWebChannel(channel)


class WebShellWindow(QMainWindow):
    """Fenêtre principale UI web."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Markdown Converter")
        self.resize(960, 640)

        self._backend = WebBackend(self)
        self._view = QWebEngineView(self)
        _configure_web_settings(self._view)
        _register_web_channel(self._view, self._backend)
        self.setCentralWidget(self._view)
        self._view.load(resolve_web_index_url())


def run_app() -> None:
    """Lance l'UI web (PySide6 + WebEngine + build ``web/dist``)."""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        print(
            "L'UI web requiert PySide6.\nInstallez : pip install -r requirements-qt.txt",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    try:
        import PySide6.QtWebEngineWidgets  # noqa: F401
    except ImportError as exc:
        print(
            "Qt WebEngineWidgets est indisponible.\n"
            "Voir spike/webengine/README.md (dépendances Linux).",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    try:
        resolve_web_index_url()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    app = QApplication.instance() or QApplication(sys.argv)
    window = WebShellWindow()
    window.show()
    sys.exit(app.exec())
