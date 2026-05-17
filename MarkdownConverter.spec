# -*- mode: python ; coding: utf-8 -*-
"""
Fichier de build PyInstaller pour macOS (.app) et Linux (dossier onedir).

Usage :
  ./scripts/build_web.sh
  pyinstaller --noconfirm MarkdownConverter.spec

PLO-55 : inclut Qt WebEngine, le front ``web/dist`` et l'UI web par défaut dans le bundle.
"""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None

datas: list = []
binaries: list = []
hiddenimports: list = []

md_datas, md_binaries, md_hidden = collect_all("markitdown")
datas += md_datas
binaries += md_binaries
hiddenimports += md_hidden

# MarkItDown s'appuie sur magika (détection de type) ; les fichiers model.onnx ne
# sont pas tirés par collect_all("markitdown") — requis pour PDF et autres formats.
magika_datas, magika_binaries, magika_hidden = collect_all("magika")
datas += magika_datas
binaries += magika_binaries
hiddenimports += magika_hidden

_web_dist = Path("web/dist")
if not (_web_dist / "index.html").is_file():
    raise SystemExit(
        "ERREUR : web/dist/index.html absent.\n"
        "Construisez le front : ./scripts/build_web.sh"
    )
datas += [(str(_web_dist), "web/dist")]

# UI web (PLO-46+) + repli Qt widgets (PLO-54). Les hooks PyInstaller collectent
# QtWebEngineProcess et les ressources via les hiddenimports WebEngine.
hiddenimports += [
    "ui_web_shell",
    "ui_web_bootstrap",
    "ui_web_loaders",
    "ui_web_drop",
    "ui_web_engine_env",
    "conversion_queue",
    "conversion_mime_paths",
    "bridge_contract",
    "bridge_contract.models",
    "bridge_contract.inspector_helpers",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebChannel",
    "PySide6.QtPrintSupport",
    "ui_qt_conversion_worker",
    "ui_qt_file_model",
    "ui_qt_inspector_data",
    "ui_qt_inspector_rename",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["packaging/pyi_rth_webengine.py"],
    excludes=[
        # Modules Qt lourds ou inutiles pour l'UI actuelle (WebEngine conservé).
        "PySide6.Qt3DAnimation",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DExtras",
        "PySide6.Qt3DInput",
        "PySide6.Qt3DLogic",
        "PySide6.Qt3DRender",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtQuick",
        "PySide6.QtQml",
        "PySide6.QtQuickWidgets",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "PySide6.QtLocation",
        "PySide6.QtPositioning",
        "PySide6.QtBluetooth",
        "PySide6.QtNfc",
        "PySide6.QtSerialPort",
        "PySide6.QtWebSockets",
        "PySide6.QtWebEngineQuick",
        # Outils de dev tirés par markitdown / analyse — inutiles dans le bundle.
        "pytest",
        "_pytest",
        "py",
        "pygments",
        "pluggy",
        "iniconfig",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Markdown Converter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Markdown Converter",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Markdown Converter.app",
        icon=None,
        bundle_identifier="io.github.zitdantes.markdownconverter",
        info_plist={
            "NSPrincipalClass": "NSApplication",
            "NSHighResolutionCapable": "True",
            "LSEnvironment": {
                "MARKDOWN_CONVERTER_UI": "web",
                "QTWEBENGINE_DISABLE_SANDBOX": "1",
                "QTWEBENGINE_CHROMIUM_FLAGS": "--no-sandbox",
            },
        },
    )
