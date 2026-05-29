# -*- mode: python ; coding: utf-8 -*-
"""
MangaRecap PyInstaller Spec - Single File Mode
Generates a single standalone Windows executable.
Note: One-file mode may have longer startup times.
"""

import sys
import os

block_cipher = None
project_root = os.path.abspath(SPECDIR)

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'core'), 'core'),
        (os.path.join(project_root, 'gui'), 'gui'),
    ],
    hiddenimports=[
        'core.manga_extraction',
        'core.vision_analysis',
        'core.narration',
        'core.movie_director',
        'core.config_manager',
        'core.worker',
        'gui.styles',
        'gui.main_window',
        'gui.new_project_page',
        'gui.library_page',
        'gui.settings_page',
        'PyQt6.sip',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'fitz',
        'PyMuPDF',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'cv2',
        'numpy',
        'openai',
        'requests',
        'moviepy',
        'moviepy.editor',
        'moviepy.video.fx.all',
        'elevenlabs',
        'soundfile',
        'edge_tts',
        'cryptography',
        'cryptography.fernet',
        'appdirs',
        'tqdm',
        'kokoro',
        'huggingface_hub',
        'pyttsx3',
        'comtypes',
        'packaging',
        'packaging.version',
        'packaging.specifiers',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'PySide6',
        'PyQt5',
        'shiboken6',
        'pydoc',
        'test',
        '_test',
        'pytest',
        'unittest',
    ],
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
    name='MangaRecap',
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
    icon=os.path.join(project_root, 'resources', 'icon.ico'),
)
