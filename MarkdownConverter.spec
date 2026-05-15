# -*- mode: python ; coding: utf-8 -*-
"""
Fichier de build PyInstaller pour macOS (.app sans console).
Usage : pyinstaller MarkdownConverter.spec
"""
from PyInstaller.utils.hooks import collect_all

block_cipher = None

datas: list = []
binaries: list = []
hiddenimports: list = []

md_datas, md_binaries, md_hidden = collect_all("markitdown")
datas += md_datas
binaries += md_binaries
hiddenimports += md_hidden

# PLO-58 / v0.2 : modules UI Qt (pas collect_all PySide6 — évite WebEngine/QML ~1 Go).
hiddenimports += [
    "ui_qt",
    "ui_qt_conversion_worker",
    "ui_qt_file_model",
    "ui_qt_file_proxy",
    "ui_qt_file_drop_table",
    "ui_qt_inspector",
    "ui_qt_inspector_data",
    "ui_qt_inspector_rename",
    "ui_qt_journal",
    "ui_qt_settings",
    "ui_qt_theme",
]

a = Analysis(
    ["main.py", "ui_qt.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Modules Qt lourds ou inutiles pour l'UI widgets actuelle.
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
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
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name="Markdown Converter",
)

app = BUNDLE(
    coll,
    name="Markdown Converter.app",
    icon=None,
    bundle_identifier="io.github.zitdantes.markdownconverter",
    info_plist={
        "NSPrincipalClass": "NSApplication",
        "NSHighResolutionCapable": "True",
        # Interface Qt par défaut dans le bundle (équivalent MARKDOWN_CONVERTER_UI=qt).
        "LSEnvironment": {
            "MARKDOWN_CONVERTER_UI": "qt",
        },
    },
)
