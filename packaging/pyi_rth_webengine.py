# Runtime hook PyInstaller (PLO-55) — Qt WebEngine dans un bundle gelé.
# Sans ceci, Chromium abort souvent au premier QWebEnginePage (sandbox / chemins).


def _pyi_rthook() -> None:
    import os

    os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
    flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "").strip()
    if "--no-sandbox" not in flags.split():
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = f"{flags} --no-sandbox".strip()


_pyi_rthook()
del _pyi_rthook
