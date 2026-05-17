# Runtime hook PyInstaller (PLO-55) — Qt WebEngine dans un bundle gelé.
# Sans ceci, Chromium abort souvent au premier QWebEnginePage (sandbox / chemins).


def _pyi_rthook() -> None:
    from ui_web_engine_env import configure_webengine_runtime_env

    configure_webengine_runtime_env()


_pyi_rthook()
del _pyi_rthook
