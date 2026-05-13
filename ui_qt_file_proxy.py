"""
Proxy de filtre Qt pour la file de conversion (PLO-36).

Filtre le ``ConversionFileTableModel`` selon deux critères cumulatifs :

1. **Extensions actives** (set vide = aucun filtre, *tout passe*). La politique
   "tout vide = tout affiché" est explicite : décocher toutes les chips affiche
   à nouveau la totalité de la file, ce qui évite l'écueil "j'ai décoché par
   erreur, je ne vois plus rien".
2. **Sous-chaîne du nom de fichier** (insensible à la casse, vide = pas de
   filtre).

Le proxy émet ``filter_changed`` à chaque mutation des critères et chaque
``invalidateFilter`` ; pratique pour les compteurs des chips ou le footer.
"""

from __future__ import annotations

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel, Signal

from ui_qt_file_model import ConversionFileTableModel
from utils import normalize_extension


class ConversionFileFilterProxy(QSortFilterProxyModel):
    """``QSortFilterProxyModel`` filtrant par extensions + sous-chaîne du nom."""

    filter_changed = Signal()

    def __init__(self, source_model: ConversionFileTableModel) -> None:
        super().__init__()
        self._active_extensions: set[str] = set()
        self._name_filter: str = ""
        self.setSourceModel(source_model)
        # Le tri reste géré par le modèle source ; on garde la sélection live
        # quand la liste est triée par l'utilisateur.
        self.setDynamicSortFilter(True)

    def set_active_extensions(self, extensions: set[str]) -> None:
        """Active uniquement ces extensions. Set vide = pas de filtre par format."""
        normalized = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}
        if normalized == self._active_extensions:
            return
        self._active_extensions = normalized
        self.invalidate()
        self.filter_changed.emit()

    def active_extensions(self) -> set[str]:
        return set(self._active_extensions)

    def set_name_filter(self, query: str) -> None:
        """Filtre par sous-chaîne du nom de fichier (insensible à la casse)."""
        cleaned = (query or "").strip().lower()
        if cleaned == self._name_filter:
            return
        self._name_filter = cleaned
        self.invalidate()
        self.filter_changed.emit()

    def name_filter(self) -> str:
        return self._name_filter

    def source_record_at(self, proxy_row: int) -> object | None:
        """Retourne le ``FileConversionRecord`` source pour une ligne du proxy."""
        proxy_index = self.index(proxy_row, 0)
        if not proxy_index.isValid():
            return None
        source_index = self.mapToSource(proxy_index)
        if not source_index.isValid():
            return None
        records = self._source_records()
        if records is None:
            return None
        row = source_index.row()
        if 0 <= row < len(records):
            return records[row]
        return None

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        records = self._source_records()
        if records is None or not (0 <= source_row < len(records)):
            return False
        rec = records[source_row]
        path = rec.source_path
        if self._active_extensions and normalize_extension(path) not in self._active_extensions:
            return False
        if self._name_filter and self._name_filter not in path.name.lower():
            return False
        _ = source_parent
        return True

    def _source_records(self) -> list[object] | None:
        source = self.sourceModel()
        if isinstance(source, ConversionFileTableModel):
            return source.records()
        return None
