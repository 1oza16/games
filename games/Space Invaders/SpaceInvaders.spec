# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_dir = Path(SPECPATH)
project_root = project_dir.parent.parent

a = Analysis(
    [str(project_dir / 'main.py')],
    pathex=[],
    binaries=[],
    datas=[
        (str(project_dir / 'img'), 'img'),
        (str(project_dir / 'audio'), 'audio'),
        (str(project_dir / 'data' / 'records.json'), 'data'),
        (str(project_root / 'docs' / 'sound' / 'Space Invaders'), 'audio/music'),
    ],
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
    name='SpaceInvaders',
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
    icon=str(project_dir / 'img' / 'space invaders - favicon.ico'),
)
