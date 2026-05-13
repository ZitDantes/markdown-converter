"""
Hiérarchie d'exceptions métier de l'orchestrateur de conversion.

Ces exceptions sont levées (ou capturées) par ``converter.py`` lors du traitement
d'un lot de fichiers. Elles complètent les exceptions internes aux moteurs
définies dans :mod:`engines.base` (``EngineError`` et ses sous-classes) :

* ``EngineError`` (côté moteur) : un moteur précis a échoué ou n'est pas disponible.
* ``ConverterError`` (ici) : l'orchestrateur a pris une décision métier, par exemple
  « tous les moteurs ont échoué » ou « le Markdown produit est vide après nettoyage ».

Cette séparation permet d'ajouter de nouveaux moteurs sans toucher ``errors.py``,
et de faire évoluer l'orchestration sans toucher ``engines/``.
"""

from __future__ import annotations


class ConverterError(Exception):
    """Base de toutes les erreurs métier de l'orchestrateur de conversion."""


class UnsupportedFormatError(ConverterError):
    """Le format du fichier source n'est pas supporté par l'application."""


class EngineFailureError(ConverterError):
    """
    Tous les moteurs disponibles ont échoué sur un fichier.

    ``engine_tried`` indique le dernier moteur essayé (utile pour le rapport).
    ``cause`` enveloppe l'exception d'origine côté moteur (souvent un ``EngineConversionError``).
    """

    def __init__(
        self,
        message: str,
        engine_tried: str,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.engine_tried = engine_tried
        self.cause = cause


class EmptyConversionError(ConverterError):
    """La conversion a réussi mais a produit un Markdown vide après nettoyage."""


class OutputWriteError(ConverterError):
    """Impossible d'écrire le fichier Markdown de sortie sur le disque."""
