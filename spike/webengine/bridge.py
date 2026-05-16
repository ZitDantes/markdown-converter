"""Pont Python minimal pour le spike QWebChannel (PLO-44)."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot


class SpikeBridge(QObject):
    """Objet exposé au JavaScript via ``QWebChannel``."""

    logFromJs = Signal(str)

    @Slot(str, result=str)
    def ping(self, message: str) -> str:
        """Répond à un message JS ; utilisé pour valider le pont."""
        text = (message or "").strip()
        self.logFromJs.emit(text)
        return f"pong:{text or 'vide'}"

    @Slot(result=str)
    def loaderLabel(self) -> str:
        """Indique le mode de chargement actif (``file`` ou ``qrc``)."""
        return getattr(self, "_loader_label", "inconnu")

    def set_loader_label(self, label: str) -> None:
        self._loader_label = label
