"""
Tests unitaires de ``engines.pandoc_engine``.

Ces tests **ne dépendent pas** d'une installation réelle de Pandoc : la
détection (``shutil.which``) et l'exécution (``subprocess.run``) sont
systématiquement monkeypatchées. Les tests d'intégration réels (qui dépendent
d'un binaire ``pandoc`` présent dans le PATH) vivent dans
``tests/integration/test_pandoc_real.py``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from engines import EngineConversionError, EngineNotAvailableError
from engines import pandoc_engine as pe
from engines.pandoc_engine import (
    DEFAULT_PANDOC_TIMEOUT_S,
    PandocEngine,
    _resolve_timeout_s,
)

_FAKE_PANDOC = "/usr/local/bin/pandoc"


@pytest.fixture
def with_pandoc(monkeypatch: pytest.MonkeyPatch) -> str:
    """Fait croire à ``shutil.which`` que pandoc est installé à ``_FAKE_PANDOC``."""
    monkeypatch.setattr(pe.shutil, "which", lambda name: _FAKE_PANDOC if name == "pandoc" else None)
    return _FAKE_PANDOC


@pytest.fixture
def without_pandoc(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fait croire à ``shutil.which`` que pandoc n'est nulle part."""
    monkeypatch.setattr(pe.shutil, "which", lambda _name: None)


class TestAvailability:
    def test_is_available_true_when_binary_present(self, with_pandoc: str) -> None:
        assert PandocEngine.is_available() is True

    def test_is_available_false_when_binary_absent(self, without_pandoc: None) -> None:
        assert PandocEngine.is_available() is False

    def test_executable_path_returns_which_result(self, with_pandoc: str) -> None:
        assert PandocEngine.executable_path() == _FAKE_PANDOC

    def test_executable_path_none_when_absent(self, without_pandoc: None) -> None:
        assert PandocEngine.executable_path() is None

    def test_init_raises_when_binary_absent(self, without_pandoc: None) -> None:
        with pytest.raises(EngineNotAvailableError, match="Pandoc n'est pas installé"):
            PandocEngine()


class TestSupports:
    @pytest.mark.parametrize(
        "ext",
        [".docx", ".pptx", ".pdf", ".html", ".htm", ".txt", ".HTML"],
    )
    def test_supports_known_extensions(self, with_pandoc: str, ext: str) -> None:
        assert PandocEngine().supports(Path(f"sample{ext}")) is True

    @pytest.mark.parametrize("ext", [".xlsx", ".xyz", "", ".png"])
    def test_does_not_support_unknown_extensions(self, with_pandoc: str, ext: str) -> None:
        assert PandocEngine().supports(Path(f"sample{ext}")) is False


class TestResolveTimeout:
    """``_resolve_timeout_s`` lit ``PANDOC_TIMEOUT_S`` et tombe sur la valeur par défaut sinon."""

    def test_default_when_env_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PANDOC_TIMEOUT_S", raising=False)
        assert _resolve_timeout_s() == DEFAULT_PANDOC_TIMEOUT_S

    def test_uses_env_when_valid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PANDOC_TIMEOUT_S", "5")
        assert _resolve_timeout_s() == 5

    def test_default_when_env_not_numeric(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PANDOC_TIMEOUT_S", "abc")
        assert _resolve_timeout_s() == DEFAULT_PANDOC_TIMEOUT_S

    @pytest.mark.parametrize("bad", ["0", "-3"])
    def test_default_when_env_non_positive(self, monkeypatch: pytest.MonkeyPatch, bad: str) -> None:
        monkeypatch.setenv("PANDOC_TIMEOUT_S", bad)
        assert _resolve_timeout_s() == DEFAULT_PANDOC_TIMEOUT_S


class TestConvert:
    """``convert()`` : on stube ``subprocess.run`` pour ne pas dépendre du binaire."""

    def test_returns_stdout_on_success(
        self, with_pandoc: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: dict[str, Any] = {}

        def fake_run(cmd: list[str], **kwargs: Any) -> SimpleNamespace:
            captured["cmd"] = cmd
            captured["timeout"] = kwargs.get("timeout")
            return SimpleNamespace(returncode=0, stdout="# Hello\n", stderr="")

        monkeypatch.setattr(pe.subprocess, "run", fake_run)
        result = PandocEngine().convert(Path("doc.html"))

        assert result == "# Hello\n"
        # On invoque bien le binaire détecté avec le bon reader.
        assert captured["cmd"][0] == _FAKE_PANDOC
        assert "--from=html" in captured["cmd"]
        assert "--to=gfm" in captured["cmd"]
        assert captured["timeout"] == DEFAULT_PANDOC_TIMEOUT_S

    def test_raises_engine_error_on_timeout(
        self, with_pandoc: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_run(cmd: list[str], **_kwargs: Any) -> SimpleNamespace:
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=60)

        monkeypatch.setattr(pe.subprocess, "run", fake_run)
        with pytest.raises(EngineConversionError, match="dépassé le délai"):
            PandocEngine().convert(Path("doc.html"))

    def test_raises_engine_error_on_non_zero_returncode(
        self, with_pandoc: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_run(_cmd: list[str], **_kwargs: Any) -> SimpleNamespace:
            return SimpleNamespace(returncode=1, stdout="", stderr="boom: invalid input\n")

        monkeypatch.setattr(pe.subprocess, "run", fake_run)
        with pytest.raises(EngineConversionError, match="boom: invalid input"):
            PandocEngine().convert(Path("doc.html"))

    def test_raises_engine_error_for_unsupported_extension(
        self, with_pandoc: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Sécurité défensive : même si l'orchestrateur ne devrait pas appeler convert()
        # sur un format non géré, le moteur doit échouer proprement.
        def fake_run(*_args: Any, **_kwargs: Any) -> SimpleNamespace:
            raise AssertionError("subprocess ne doit pas être appelé pour un format non supporté")

        monkeypatch.setattr(pe.subprocess, "run", fake_run)
        with pytest.raises(EngineConversionError, match="lecteur"):
            PandocEngine().convert(Path("sheet.xlsx"))
