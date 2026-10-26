# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Resource Path Resolution Utility

Provides PyInstaller-compatible path resolution for resources.
Handles both development and bundled executable environments.
"""

import os
import sys
from pathlib import Path


def get_base_path() -> Path:
    """
    Get the base path for resources, handling both development and PyInstaller environments.

    Priority order:
    1. ``SATYA_BASE_PATH`` env var - set by the student launcher scripts
       (install_satya.ps1 written satya.cmd/satya-gui.cmd) so a pip-installed
       app resolves ``satya_data`` in the student workspace, not in
       site-packages.
    2. PyInstaller bundle root (``sys.frozen``).
    3. Repo root when running from a checkout (package parent).

    Returns:
        Path: Base path to the application resources
    """
    env_base = os.environ.get("SATYA_BASE_PATH")
    if env_base:
        return Path(env_base).resolve()

    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        this_file = Path(__file__).resolve()
        base_path = this_file.parent.parent.parent

    return base_path


def resolve_content_dir(relative_path: str) -> Path:
    """
    Resolve the content directory path.

    Args:
        relative_path (str): Relative path from base (e.g., "satya_data/content")

    Returns:
        Path: Resolved absolute path to content directory
    """
    base_path = get_base_path()
    resolved = base_path / relative_path

    if not resolved.exists() and not getattr(sys, "frozen", False):
        project_root = base_path
        resolved = project_root / relative_path

        if not resolved.exists():
            fallback = project_root / "scripts" / "data_collection" / "data" / "content"
            if fallback.exists():
                return fallback

    return resolved


def resolve_model_dir(relative_path: str) -> Path:
    """
    Resolve the model directory path.

    Args:
        relative_path (str): Relative path from base (e.g., "satya_data/models/phi_1_5")

    Returns:
        Path: Resolved absolute path to model directory
    """
    base_path = get_base_path()
    resolved = base_path / relative_path

    if not resolved.exists() and not getattr(sys, "frozen", False):
        project_root = base_path
        resolved = project_root / relative_path

    return resolved


def resolve_chroma_db_dir(relative_path: str = "satya_data/chroma_db") -> Path:
    """
    Resolve the ChromaDB directory path.

    Args:
        relative_path (str): Relative path from base (default: "satya_data/chroma_db")

    Returns:
        Path: Resolved absolute path to ChromaDB directory
    """
    base_path = get_base_path()
    resolved = base_path / relative_path

    if not resolved.exists() and not getattr(sys, "frozen", False):
        project_root = base_path
        resolved = project_root / relative_path

    return resolved
