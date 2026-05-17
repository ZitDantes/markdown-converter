"""Tests du choix d'UI au démarrage (PLO-55)."""

from __future__ import annotations

import sys

import pytest

from main import UI_ENV_VAR, UI_TK, UI_WEB, _resolve_ui_choice


def test_resolve_ui_choice_frozen_defaults_to_web(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(UI_ENV_VAR, raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert _resolve_ui_choice() == UI_WEB


def test_resolve_ui_choice_dev_defaults_to_tk(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(UI_ENV_VAR, raising=False)
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    assert _resolve_ui_choice() == UI_TK
