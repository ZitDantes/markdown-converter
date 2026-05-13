"""
Tests unitaires des helpers de ``converter`` qui ne nécessitent pas de moteur.
"""

from __future__ import annotations

import pytest

from converter import ConversionStatus, _resolve_success_status


@pytest.mark.parametrize(
    ("fmt_warning", "used_fallback", "expected"),
    [
        (None, False, ConversionStatus.SUCCESS),
        (None, True, ConversionStatus.SUCCESS_FALLBACK),
        ("Relecture recommandée", False, ConversionStatus.SUCCESS_REVIEW),
        ("Relecture recommandée", True, ConversionStatus.SUCCESS_REVIEW),
    ],
)
def test_resolve_success_status(
    fmt_warning: str | None,
    used_fallback: bool,
    expected: ConversionStatus,
) -> None:
    """
    Règle de priorité : ``SUCCESS_REVIEW`` > ``SUCCESS_FALLBACK`` > ``SUCCESS``.

    En particulier, le cas (avertissement + fallback) reste ``SUCCESS_REVIEW`` :
    l'info utilisateur (« à relire ») prime sur l'info technique (« secours »).
    Le drapeau ``used_pandoc_fallback`` continue d'être renseigné sur le record
    pour les UI qui veulent afficher les deux.
    """
    assert _resolve_success_status(fmt_warning, used_fallback) is expected
