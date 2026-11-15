# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

project_dir = Path(SPECPATH)
project_root = project_dir.parent.parent
app_name = 'SpaceInvaders'
app_version = '1.0.0'
exe_name = f'{app_name}-{app_version}-Windows-x64'

version_info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=(1, 0, 0, 0), prodvers=(1, 0, 0, 0)),
    kids=[
        StringFileInfo([
            StringTable('040904B0', [
                StringStruct('FileDescription', 'Space Invaders'),
                StringStruct('FileVersion', app_version),
                StringStruct('InternalName', app_name),
                StringStruct('OriginalFilename', f'{exe_name}.exe'),
                StringStruct('ProductName', 'Space Invaders'),
                StringStruct('ProductVersion', app_version),
            ]),
        ]),
        VarFileInfo([VarStruct('Translation', [1033, 1200])]),
    ],
)

a = Analysis(
    [str(project_dir / 'main.py')],
    pathex=[],
    binaries=[],
    datas=[
        (str(project_root / 'docs' / 'img'), 'img'),
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
    name=exe_name,
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
    version=version_info,
    entitlements_file=None,
    icon=str(project_root / 'docs' / 'img' / 'space invaders - favicon.png'),
)
