# -*- mode: python ; coding: utf-8 -*-
"""
MangaRecap PyInstaller Spec File
Generates a standalone Windows executable.
"""

import sys
import os
from pathlib import Path

block_cipher = None

# Project root
project_root = os.path.abspath(SPECDIR)

# Analysis configuration
a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        # Include all package data
        (os.path.join(project_root, 'core'), 'core'),
        (os.path.join(project_root, 'gui'), 'gui'),
        (os.path.join(project_root, 'resources'), 'resources'),
    ],
    hiddenimports=[
        # Core dependencies
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
        # PyQt6 hidden imports
        'PyQt6.sip',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        # PDF processing
        'fitz',
        'PyMuPDF',
        # Image processing
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'cv2',
        'numpy',
        # AI/ML
        'openai',
        'requests',
        # Video processing
        'moviepy',
        'moviepy.editor',
        'moviepy.video.fx.all',
        # Audio processing
        'elevenlabs',
        'soundfile',
        'edge_tts',
        # Crypto
        'cryptography',
        'cryptography.fernet',
        # Utilities
        'appdirs',
        'tqdm',
        # Edge TTS dependencies
        'edge_tts',
        # Kokoro TTS (optional)
        'kokoro',
        'huggingface_hub',
        # Pyttsx3 (optional)
        'pyttsx3',
        'comtypes',
        # Other common hidden imports
        'packaging',
        'packaging.version',
        'packaging.specifiers',
        'packaging.requirements',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
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

# Remove duplicate files
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Executable configuration
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
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Icon
    icon=os.path.join(project_root, 'resources', 'icon.ico'),
    # Version info
    version_info={
        'version': '1.0.0.0',
        'company_name': 'MangaRecap Team',
        'file_description': 'MangaRecap - Manga to Video Recap Application',
        'internal_name': 'MangaRecap',
        'legal_copyright': '© 2024 MangaRecap Team',
        'original_filename': 'MangaRecap.exe',
        'product_name': 'MangaRecap',
    },
)

# Build directory (for one-dir mode which is more reliable)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MangaRecap'
)
