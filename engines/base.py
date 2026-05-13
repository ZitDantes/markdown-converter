"""
Interface commune pour les moteurs de conversion locaux.

Chaque moteur (MarkItDown, Pandoc, …) implémente ``ConverterEngine`` et expose
les mêmes méthodes : ``is_available()``, ``supports(path)`` et ``convert(path)``.

Les exceptions custom ``EngineNotAvailableError`` et ``EngineConversionError``
permettent à l'orchestrateur de distinguer les pannes structurelles (paquet ou
binaire manquant) des échecs de conversion fichier par fichier.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class EngineError(RuntimeError):
    """Base de toutes les erreurs liées aux moteurs de conversion."""


class EngineNotAvailableError(EngineError):
    """Le moteur n'est pas utilisable sur cette machine (paquet ou binaire manquant)."""


class EngineConversionError(EngineError):
    """Le moteur a échoué à convertir un fichier (input invalide, lecteur absent, etc.)."""


class ConverterEngine(ABC):
    """
    Contrat des moteurs de conversion locaux.

    Attribut de classe ``name`` : nom court affiché dans les logs et le rapport
    (ex. ``"MarkItDown"``, ``"Pandoc"``).
    """

    name: str = "ConverterEngine"

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Le moteur est-il prêt à l'emploi sur cette machine ?"""

    @abstractmethod
    def supports(self, path: Path) -> bool:
        """Le moteur sait-il traiter ce format ?"""

    @abstractmethod
    def convert(self, path: Path) -> str:
        """Convertit ``path`` en Markdown, ou lève ``EngineConversionError``."""
