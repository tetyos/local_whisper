# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Local Whisper."""

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Get the project root
project_root = Path(SPECPATH)
icon_path = project_root / 'assets' / 'icon.ico'

# Collect data files
datas = []
datas += collect_data_files('faster_whisper')
datas += collect_data_files('huggingface_hub')

a = Analysis(
    [str(project_root / 'src' / 'entry_point.py')],
    pathex=[str(project_root / 'src')],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'faster_whisper',
        'ctranslate2',
        'huggingface_hub',
        'tokenizers',
        'sounddevice',
        'numpy',
        'keyboard',
        'pyautogui',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='local-whisper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window - runs as GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
)
