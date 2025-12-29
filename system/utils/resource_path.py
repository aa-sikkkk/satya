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
        # Running as a bundled executable (PyInstaller)
        base_path = Path(sys._MEIPASS)
    else:
        # Running as a script
        # Get the project root (3 levels up from this file: system/utils/resource_path.py)
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
    
    # If not found in base, try project root
    if not resolved.exists() and not getattr(sys, 'frozen', False):
        # In development, try project root
        project_root = base_path
        resolved = project_root / relative_path
        
        # Also try scripts/data_collection/data/content as fallback
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
    
    # If not found in base, try project root
    if not resolved.exists() and not getattr(sys, 'frozen', False):
        # In development, try project root
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
    
    # If not found in base, try project root
    if not resolved.exists() and not getattr(sys, 'frozen', False):
        # In development, try project root
        project_root = base_path
        resolved = project_root / relative_path
    
    return resolved

