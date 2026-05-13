"""
Point d'entrée : lance l'interface graphique de Markdown Converter.

L'UI par défaut est Tkinter (``ui.py``). Pour essayer le prototype PySide6,
définir ``MARKDOWN_CONVERTER_UI=qt`` avant le lancement, après avoir installé
les dépendances optionnelles ::

    pip install -r requirements-qt.txt
    MARKDOWN_CONVERTER_UI=qt python3 main.py
"""

from __future__ import annotations

import os
import sys

MIN_PYTHON = (3, 10)
UI_ENV_VAR = "MARKDOWN_CONVERTER_UI"
UI_TK = "tk"
UI_QT = "qt"


def _fail_python_version() -> None:
    msg = (
        f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} ou supérieur est requis pour MarkItDown.\n\n"
        f"Version actuelle : {sys.version.split()[0]}\n\n"
        "Installez Python 3.10+ (python.org ou « brew install python@3.12 »), puis recréez l'environnement :\n"
        "  rm -rf .venv\n"
        "  python3.12 -m venv .venv\n"
        "  source .venv/bin/activate\n"
        "  pip install --upgrade pip\n"
        "  pip install -r requirements.txt\n"
        "  python3 main.py"
    )
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Markdown Converter — version de Python", msg)
        root.destroy()
    except Exception:  # noqa: BLE001
        print(msg, file=sys.stderr)
    sys.exit(1)


def _fail_tkinter(exc: BaseException | None = None) -> None:
    """
    Homebrew installe ``python@3.x`` sans Tkinter ; il faut ``python-tk@3.x`` en plus.
    On n'utilise pas Tk ici pour afficher l'erreur (il est précisément absent).
    """
    major, minor = sys.version_info.major, sys.version_info.minor
    msg = (
        "Tkinter n'est pas disponible pour ce Python (module « _tkinter » introuvable).\n\n"
        "Avec Python installé via Homebrew, installez le paquet Tk correspondant à la même version, par exemple :\n\n"
        f"  brew install python-tk@{major}.{minor}\n\n"
        "Puis recréez l'environnement virtuel avec **le même** exécutable Python :\n\n"
        f"  rm -rf .venv\n"
        f"  python{major}.{minor} -m venv .venv\n"
        "  source .venv/bin/activate\n"
        "  pip install -r requirements.txt\n"
        "  python3 main.py\n\n"
        f"Interpréteur utilisé : {sys.executable}\n"
    )
    if exc:
        msg += f"\nDétail : {exc}\n"
    print(msg, file=sys.stderr)
    sys.exit(1)


def _resolve_ui_choice() -> str:
    """Lit ``MARKDOWN_CONVERTER_UI`` ; valeurs ignorées (typo, vide) → ``tk``."""
    raw = os.environ.get(UI_ENV_VAR, "").strip().lower()
    return UI_QT if raw == UI_QT else UI_TK


def _run_qt_ui() -> bool:
    """Tente de lancer l'UI PySide6 ; retourne ``True`` si elle a tourné.

    Si PySide6 n'est pas installé, on prévient et on retourne ``False`` pour
    que ``main()`` retombe sur l'UI Tkinter (au lieu de planter l'app).
    """
    try:
        from ui_qt import run_app as run_qt_app
    except ImportError as e:
        print(
            f"{UI_ENV_VAR}=qt demandé mais PySide6 est introuvable.\n"
            "Installez-le avec : pip install -r requirements-qt.txt\n"
            f"Bascule vers l'interface Tkinter par sécurité.\nDétail : {e}",
            file=sys.stderr,
        )
        return False
    run_qt_app()
    return True


def main() -> None:
    if sys.version_info < MIN_PYTHON:
        _fail_python_version()

    ui_choice = _resolve_ui_choice()

    if ui_choice == UI_QT:
        from logging_setup import get_logger, setup_logging

        log_path = setup_logging()
        get_logger("main").info(
            "Démarrage de l'application (UI Qt, logs : %s).",
            log_path,
        )
        if _run_qt_ui():
            return
        # Sinon : on tombe sur le chemin Tk ci-dessous.

    try:
        import tkinter  # noqa: F401
    except ImportError as e:
        _fail_tkinter(e)

    from logging_setup import get_logger, setup_logging

    log_path = setup_logging()
    get_logger("main").info("Démarrage de l'application (UI Tk, logs : %s).", log_path)

    from ui import run_app

    run_app()


if __name__ == "__main__":
    main()
