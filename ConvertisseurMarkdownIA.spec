# -*- mode: python ; coding: utf-8 -*-
"""
Fichier de build PyInstaller pour macOS (.app sans console).
Usage : pyinstaller ConvertisseurMarkdownIA.spec
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

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Convertisseur Markdown IA",
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
    name="Convertisseur Markdown IA",
)

app = BUNDLE(
    coll,
    name="Convertisseur Markdown IA.app",
    icon=None,
    bundle_identifier="org.convertisseur.markdownia",
    info_plist={
        "NSPrincipalClass": "NSApplication",
        "NSHighResolutionCapable": "True",
    },
)
