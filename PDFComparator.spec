# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PDF Comparator application.
This file configures how PyInstaller builds the executable.
"""

import sys
from pathlib import Path
import os

block_cipher = None

# Get the base directory (current directory where spec file is located)
base_dir = Path(os.path.dirname(os.path.abspath(SPECPATH)))

# Collect Tcl/Tk data files for tkinter
# In Windows, Tcl/Tk files are in the Python root directory under 'tcl' folder
import sys
python_root = Path(sys.prefix)
tcl_path = python_root / 'tcl'

# Collect all Python files in the project
a = Analysis(
    ['menu_principal.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include config.json if it exists
    ] + ([(str(Path('config.json')), '.')] if Path('config.json').exists() else []) + (
        # Include Tcl/Tk data files (entire tcl directory contains both tcl8.6 and tk8.6)
        [(str(tcl_path), 'tcl')] if tcl_path.exists() else []
    ),
    hiddenimports=[
        # Core modules
        'menu_principal',
        'interfaz_archivos',
        'interfaz_carpetas',
        'funciones_comparador',
        'configuracion',
        # Tkinter dependencies
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        # PyMuPDF
        'fitz',
        # OpenCV
        'cv2',
        # PIL/Pillow
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        # NumPy
        'numpy',
        'numpy.lib.format',
        # Joblib
        'joblib',
        'joblib.externals.loky',
        'joblib.externals.loky.backend',
        # PyPDF2
        'PyPDF2',
        # Standard library modules that might be needed
        'multiprocessing',
        'multiprocessing.pool',
        'threading',
        'gc',
        'json',
        'dataclasses',
        'pathlib',
        'difflib',
        'contextlib',
        'logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'pandas',
        'scipy',
        'jupyter',
        'IPython',
        'pytest',
        'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PDFCompare',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: 'icon.ico'
)

