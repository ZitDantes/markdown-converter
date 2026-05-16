"""Tests logique journal (miroir du module TS ``logJournal``)."""

from __future__ import annotations

# Reproduit les règles de filtrage côté front pour éviter une dérive silencieuse.


def _normalize(level: str) -> str:
    u = level.strip().upper()
    if u in ("WARN", "WARNING"):
        return "WARNING"
    if u == "INFO":
        return "INFO"
    if u == "ERROR":
        return "ERROR"
    if u == "OK":
        return "OK"
    return "UNKNOWN"


def _filter_entries(entries: list[tuple[str, str]], filt: str) -> list[tuple[str, str]]:
    if filt == "all":
        return entries
    if filt == "info":
        return [e for e in entries if e[0] in ("INFO", "OK")]
    if filt == "warn":
        return [e for e in entries if e[0] == "WARNING"]
    return [e for e in entries if e[0] == "ERROR"]


def test_filter_warn_hides_info() -> None:
    entries = [
        (_normalize("INFO"), "a"),
        (_normalize("WARNING"), "b"),
    ]
    visible = _filter_entries(entries, "warn")
    assert len(visible) == 1
    assert visible[0][1] == "b"
