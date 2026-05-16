"""
Fenêtre spike PLO-44 : QWebEngineView + QWebChannel, chargement file: ou qrc:.

Lancement ::
    MARKDOWN_CONVERTER_UI=web-spike python3 main.py
    MARKDOWN_CONVERTER_SPIKE_LOADER=qrc MARKDOWN_CONVERTER_UI=web-spike python3 main.py

Mesures optionnelles (console) ::
    MARKDOWN_CONVERTER_SPIKE_BENCHMARK=1 MARKDOWN_CONVERTER_UI=web-spike python3 main.py
"""

from __future__ import annotations

import os
import sys
import time

from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow

from spike.webengine.bridge import SpikeBridge
from spike.webengine.loaders import LoaderMode, resolve_page_url

SPIKE_ENV_LOADER = "MARKDOWN_CONVERTER_SPIKE_LOADER"
SPIKE_ENV_BENCHMARK = "MARKDOWN_CONVERTER_SPIKE_BENCHMARK"


def _parse_loader_mode() -> LoaderMode:
    raw = os.environ.get(SPIKE_ENV_LOADER, LoaderMode.FILE.value).strip().lower()
    if raw == LoaderMode.QRC.value:
        return LoaderMode.QRC
    return LoaderMode.FILE


def _benchmark_enabled() -> bool:
    return os.environ.get(SPIKE_ENV_BENCHMARK, "").strip().lower() in ("1", "true", "yes")


def _configure_web_settings(view: QWebEngineView) -> None:
    from PySide6.QtWebEngineCore import QWebEngineSettings

    settings = view.page().settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
    settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, False)


def _register_web_channel(view: QWebEngineView, bridge: SpikeBridge) -> None:
    from PySide6.QtWebChannel import QWebChannel

    channel = QWebChannel(view.page())
    channel.registerObject("bridge", bridge)
    view.page().setWebChannel(channel)


class WebEngineSpikeWindow(QMainWindow):
    """Fenêtre minimale pour valider WebEngine + pont JS."""

    def __init__(self, mode: LoaderMode) -> None:
        super().__init__()
        self._mode = mode
        self._t0 = time.perf_counter()
        self.setWindowTitle("Markdown Converter — spike WebEngine (PLO-44)")
        self.resize(720, 520)

        self._bridge = SpikeBridge()
        self._bridge.set_loader_label(mode.value)

        self._view = QWebEngineView(self)
        _configure_web_settings(self._view)
        _register_web_channel(self._view, self._bridge)
        self.setCentralWidget(self._view)

        self._bridge.logFromJs.connect(self._on_log_from_js)
        self._view.loadFinished.connect(self._on_load_finished)

        self._view.load(resolve_page_url(mode))

    def _on_log_from_js(self, message: str) -> None:
        print(f"[spike][js] {message}", flush=True)

    def _on_load_finished(self, ok: bool) -> None:
        elapsed_ms = (time.perf_counter() - self._t0) * 1000
        status = "OK" if ok else "ÉCHEC"
        print(
            f"[spike] Chargement {self._mode.value}: {status} ({elapsed_ms:.0f} ms)",
            flush=True,
        )
        if _benchmark_enabled():
            print(
                f"[spike][benchmark] mode={self._mode.value} load_ms={elapsed_ms:.1f}",
                flush=True,
            )


def run_app() -> None:
    """Point d'entrée du spike (nécessite PySide6 + Qt WebEngine)."""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        print(
            "Le spike WebEngine requiert PySide6.\nInstallez : pip install -r requirements-qt.txt",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    try:
        import PySide6.QtWebEngineWidgets  # noqa: F401
    except ImportError as exc:
        print(
            "Qt WebEngineWidgets est indisponible pour cette installation PySide6.\n"
            "Sous Linux, installez les bibliothèques listées dans spike/webengine/README.md.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    mode = _parse_loader_mode()
    app = QApplication.instance() or QApplication(sys.argv)
    if _benchmark_enabled():
        t_start = time.perf_counter()
    window = WebEngineSpikeWindow(mode)
    window.show()
    if _benchmark_enabled():
        startup_ms = (time.perf_counter() - t_start) * 1000
        print(f"[spike][benchmark] show_window_ms={startup_ms:.1f}", flush=True)
    app.exec()
