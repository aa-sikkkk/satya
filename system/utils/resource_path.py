# Copyright (C) 2026 Aashik
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
    
    Returns:
        Path: Base path to the application resources
    """
    if getattr(sys, 'frozen', False):
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
    
    if not resolved.exists() and not getattr(sys, 'frozen', False):
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
    
    if not resolved.exists() and not getattr(sys, 'frozen', False):
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
    
    if not resolved.exists() and not getattr(sys, 'frozen', False):
        project_root = base_path
        resolved = project_root / relative_path
    
    return resolved

