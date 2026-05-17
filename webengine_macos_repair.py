"""
Répare la disposition de ``QtWebEngineCore.framework`` après PyInstaller (macOS).

PyInstaller peut placer ``Helpers`` et les ressources Chromium sous
``Versions/Resources/`` au lieu de ``Versions/A/``, ce qui casse le lancement
du .app (processus et ``icudtl.dat`` introuvables).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def qt_webengine_framework_dir(app_bundle: Path) -> Path | None:
    """Chemin vers ``QtWebEngineCore.framework`` dans un ``.app`` macOS."""
    fw = (
        app_bundle
        / "Contents"
        / "Frameworks"
        / "PySide6"
        / "Qt"
        / "lib"
        / "QtWebEngineCore.framework"
    )
    return fw if fw.is_dir() else None


def repair_qt_webengine_framework(framework: Path) -> bool:
    """
    Copie ``Helpers`` et ressources Chromium vers ``Versions/A/`` si besoin.

    Retourne ``True`` si une réparation a été effectuée.
    """
    versions = framework / "Versions"
    target = versions / "A"
    stray = versions / "Resources"
    if not target.is_dir() or not stray.is_dir():
        return False

    changed = False
    src_helpers = stray / "Helpers"
    dst_helpers = target / "Helpers"
    if src_helpers.is_dir() and not dst_helpers.is_dir():
        shutil.copytree(src_helpers, dst_helpers, symlinks=True)
        changed = True

    src_res = stray / "Resources"
    dst_res = target / "Resources"
    if src_res.is_dir():
        dst_res.mkdir(parents=True, exist_ok=True)
        for item in src_res.iterdir():
            dest = dst_res / item.name
            if dest.exists():
                continue
            if item.is_dir():
                shutil.copytree(item, dest, symlinks=True)
            else:
                shutil.copy2(item, dest)
            changed = True

    return changed


def repair_app_bundle(app_path: Path) -> bool:
    fw = qt_webengine_framework_dir(app_path)
    if fw is None:
        return False
    return repair_qt_webengine_framework(fw)


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if len(args) != 1:
        print("Usage: python3 webengine_macos_repair.py <Markdown Converter.app>", file=sys.stderr)
        return 2
    app = Path(args[0]).expanduser().resolve()
    if not app.is_dir():
        print(f"Bundle introuvable : {app}", file=sys.stderr)
        return 1
    if repair_app_bundle(app):
        print(f"Qt WebEngine réparé dans {app}")
    else:
        print(f"Aucune réparation nécessaire pour {app}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
