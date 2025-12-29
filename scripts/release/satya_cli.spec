# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Satya CLI Application - FIXED for your structure
"""

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_dynamic_libs

block_cipher = None

# Get project root directory
if 'SPECPATH' in globals():
    spec_dir = Path(SPECPATH)
else:
    spec_dir = Path(os.path.abspath(__file__)).parent

project_root = spec_dir.parent.parent

# Verify project structure
if not (project_root / "student_app").exists():
    raise RuntimeError(f"Project root not found: {project_root}")

# CRITICAL FIX 1: Collect llama-cpp-python native libraries
binaries = []
try:
    llama_binaries = collect_dynamic_libs('llama_cpp')
    binaries.extend(llama_binaries)
    print(f"[INFO] Found llama-cpp binaries: {[b[0] for b in llama_binaries]}")
except Exception as e:
    print(f"[WARNING] Could not collect llama-cpp binaries: {e}")

# Data files - FIXED for your actual structure
datas = []

# CRITICAL FIX 2: Your actual model path
model_files_found = []
models_path = project_root / "satya_data" / "models" / "phi_1_5"  # Your path
if models_path.exists():
    for model_file in models_path.glob("*.gguf"):
        model_files_found.append(model_file)
        datas.append((str(model_file), "satya_data/models/phi_1_5"))  # Preserve structure
        print(f"[INFO] Found model: {model_file.name}")
    
    if not model_files_found:
        print(f"[WARNING] No .gguf files found in {models_path}")
        print("[HINT] Make sure you have a .gguf file in satya_data/models/phi_1_5/")
else:
    print(f"[WARNING] Models directory not found: {models_path}")

# CRITICAL FIX 3: Your actual ChromaDB path
chroma_db_path = project_root / "satya_data" / "chroma_db"
if chroma_db_path.exists():
    datas.append((str(chroma_db_path), "satya_data/chroma_db"))
    print(f"[INFO] Found ChromaDB at: {chroma_db_path}")
else:
    print(f"[WARNING] ChromaDB directory not found: {chroma_db_path}")

# CRITICAL FIX 4: Your actual content path
content_path = project_root / "scripts" / "data_collection" / "data" / "content"
if content_path.exists():
    datas.append((str(content_path), "satya_data/content"))
    print(f"[INFO] Found content at: {content_path}")
else:
    print(f"[WARNING] Content directory not found: {content_path}")

# Hidden imports - same as before (llama-cpp focused)
hiddenimports = [
    # Core app modules
    'student_app.main',
    'student_app.interface.cli_interface',
    'student_app.progress',
    'system.data_manager.content_manager',
    'system.rag.rag_retrieval_engine',
    'system.utils.resource_path',
    'ai_model.model_utils.model_handler',
    'ai_model.model_utils.phi15_handler',
    # llama-cpp-python (CRITICAL)
    'llama_cpp',
    'llama_cpp.llama_cpp',  # Native bindings
    'llama_cpp.llama',      # Main llama interface
    'llama_cpp.utils',      # Utility functions
    # ChromaDB
    'chromadb',
    'chromadb.config',
    'chromadb.db',
    'chromadb.api',
    # Remove torch/transformers - not needed for llama-cpp
    'numpy',
    'sentencepiece',
    'tokenizers',
    'tqdm',
    'jsonschema',
    'pydantic',
    'rich',
    'rich.console',
    'rich.panel',
    'typer',
]

# Excludes - same as before
excludes = [
    'matplotlib', 'scipy', 'pandas', 'seaborn',
    'selenium', 'webdriver-manager',
    'pytest', 'pytest-cov', 'coverage',
    'black', 'flake8', 'mypy', 'isort',
    'customtkinter', 'PIL', 'tkinter',  # GUI stuff for CLI
    # Remove these heavy ML libraries
    'torch', 'transformers', 'tensorflow', 'keras',
]

a = Analysis(
    [str(project_root / "student_app" / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,  # llama-cpp binaries included
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name='SatyaCLI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)