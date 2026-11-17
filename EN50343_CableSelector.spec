# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/emuta/Development/EN50343/main.py'],
    pathex=['C:/Users/emuta/Development/EN50343'],
    binaries=[],
    datas=[('C:/Users/emuta/Development/EN50343/.venv/Lib/site-packages/customtkinter', 'customtkinter')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='EN50343_CableSelector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
