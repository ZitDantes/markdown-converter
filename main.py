"""
Point d'entrée : lance l'interface graphique du Convertisseur Markdown IA.
"""

from __future__ import annotations

import sys

MIN_PYTHON = (3, 10)


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
        messagebox.showerror("Convertisseur Markdown IA — version de Python", msg)
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


def main() -> None:
    if sys.version_info < MIN_PYTHON:
        _fail_python_version()
    try:
        import tkinter  # noqa: F401
    except ImportError as e:
        _fail_tkinter(e)

    from logging_setup import get_logger, setup_logging

    log_path = setup_logging()
    get_logger("main").info("Démarrage de l'application (logs : %s).", log_path)

    from ui import run_app

    run_app()


if __name__ == "__main__":
    main()
